"""
Claude Code usage reader for Anthropic usage data
Reads JSONL files from ~/.claude/projects/ to get Claude usage
"""
import os
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ClaudeCodeReader:
    """Reads Claude Code usage from JSONL files"""
    
    # Claude pricing (as of 2024) - per 1M tokens
    MODEL_PRICING = {
        "claude-3-opus-20240229": {
            "input": 15.0, 
            "output": 75.0,
            "cache_creation": 18.75,  # 1.25x input
            "cache_read": 1.5         # 0.1x input
        },
        "claude-opus-4-20250514": {
            "input": 15.0, 
            "output": 75.0,
            "cache_creation": 18.75,
            "cache_read": 1.5
        },
        "claude-3.5-sonnet": {
            "input": 3.0, 
            "output": 15.0,
            "cache_creation": 3.75,
            "cache_read": 0.3
        },
        "claude-3-sonnet": {
            "input": 3.0, 
            "output": 15.0,
            "cache_creation": 3.75,
            "cache_read": 0.3
        },
        "claude-sonnet-4-20250514": {
            "input": 3.0, 
            "output": 15.0,
            "cache_creation": 3.75,
            "cache_read": 0.3
        },
        "claude-3-haiku": {
            "input": 0.25, 
            "output": 1.25,
            "cache_creation": 0.3125,
            "cache_read": 0.025
        },
        "claude-3.5-haiku": {
            "input": 0.8, 
            "output": 4.0,
            "cache_creation": 1.0,
            "cache_read": 0.08
        },
        "<synthetic>": {
            "input": 0.0, 
            "output": 0.0,
            "cache_creation": 0.0,
            "cache_read": 0.0
        },
        # Default for unknown models
        "default": {
            "input": 3.0, 
            "output": 15.0,
            "cache_creation": 3.75,
            "cache_read": 0.3
        }
    }
    
    def __init__(self):
        self.claude_dir = Path.home() / ".claude" / "projects"
        self._executor = ThreadPoolExecutor(max_workers=1)
        
    def get_token_rate_history(self, session_start: datetime, interval_minutes: int = 5) -> List[int]:
        """
        Calculate token usage rates from session history.
        Returns a list of token counts added in each interval.
        """
        rates = []
        
        # Get all entries for this session
        entries_with_time = []
        jsonl_files = glob.glob(str(self.claude_dir / "**" / "*.jsonl"), recursive=True)
        
        for file_path in jsonl_files:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                            timestamp_str = entry.get('timestamp')
                            if timestamp_str:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if timestamp.tzinfo:
                                    timestamp = timestamp.replace(tzinfo=None)
                                
                                # Only include entries from this session
                                if timestamp >= session_start:
                                    message = entry.get('message', {})
                                    usage = message.get('usage', {})
                                    if usage:
                                        input_tokens = usage.get('input_tokens', 0)
                                        output_tokens = usage.get('output_tokens', 0)
                                        total_tokens = input_tokens + output_tokens
                                        entries_with_time.append((timestamp, total_tokens))
                        except:
                            continue
            except:
                continue
        
        # Sort by timestamp
        entries_with_time.sort(key=lambda x: x[0])
        
        # Calculate rates for intervals
        if len(entries_with_time) > 1:
            current_interval_start = entries_with_time[0][0]
            current_interval_tokens = 0
            
            for i in range(1, len(entries_with_time)):
                timestamp, tokens = entries_with_time[i]
                prev_tokens = entries_with_time[i-1][1]
                tokens_added = tokens - prev_tokens
                
                # Check if we're still in the same interval
                if (timestamp - current_interval_start).total_seconds() <= interval_minutes * 60:
                    current_interval_tokens += tokens_added
                else:
                    # New interval
                    if current_interval_tokens > 0:
                        rates.append(current_interval_tokens)
                    current_interval_start = timestamp
                    current_interval_tokens = tokens_added
            
            # Add the last interval
            if current_interval_tokens > 0:
                rates.append(current_interval_tokens)
        
        return rates
    
    def get_usage_data(self, since_date: Optional[datetime] = None) -> Dict:
        """Get Claude usage data from JSONL files"""
        # If since_date is None, get all data (no date filter)
        
        # Create a new set for deduplication per call
        processed_ids: Set[str] = set()
            
        logger.info(f"Reading Claude Code usage from {self.claude_dir}")
        
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        model_breakdown = {}
        session_count = 0
        
        # Find all JSONL files
        pattern = str(self.claude_dir / "**" / "*.jsonl")
        jsonl_files = glob.glob(pattern, recursive=True)
        
        logger.info(f"Found {len(jsonl_files)} JSONL files")
        
        for file_path in jsonl_files:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                            
                        try:
                            entry = json.loads(line)
                            
                            # Check timestamp FIRST
                            if since_date is not None:
                                timestamp_str = entry.get('timestamp')
                                if timestamp_str:
                                    # Parse timestamp and ensure both are timezone-naive for comparison
                                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    # Convert to naive datetime (UTC)
                                    if timestamp.tzinfo:
                                        timestamp = timestamp.replace(tzinfo=None)
                                    if timestamp < since_date:
                                        continue
                            
                            # Only deduplicate entries within the time window
                            # Use composite key like Claude Monitor
                            message_id = entry.get('message_id') or entry.get('message', {}).get('id', '')
                            request_id = entry.get('requestId') or entry.get('request_id', '')
                            
                            if message_id and request_id:
                                entry_id = f"{message_id}:{request_id}"
                                if entry_id in processed_ids:
                                    continue
                                processed_ids.add(entry_id)
                            
                            # Extract usage data - it's nested in message
                            message = entry.get('message', {})
                            usage = message.get('usage', {})
                            
                            # Skip entries without usage data
                            if not usage:
                                continue
                                
                            input_tokens = usage.get('input_tokens', 0)
                            cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)
                            cache_read_tokens = usage.get('cache_read_input_tokens', 0)
                            output_tokens = usage.get('output_tokens', 0)
                            
                            # Get model from message
                            model = message.get('model', 'unknown')
                            
                            # Calculate cost with proper cache token pricing
                            pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING['default'])
                            input_cost = (input_tokens / 1_000_000) * pricing['input']
                            cache_creation_cost = (cache_creation_tokens / 1_000_000) * pricing.get('cache_creation', pricing['input'] * 1.25)
                            cache_read_cost = (cache_read_tokens / 1_000_000) * pricing.get('cache_read', pricing['input'] * 0.1)
                            output_cost = (output_tokens / 1_000_000) * pricing['output']
                            item_cost = input_cost + cache_creation_cost + cache_read_cost + output_cost
                            
                            # Update totals
                            total_cost += item_cost
                            total_input_tokens += input_tokens + cache_creation_tokens + cache_read_tokens
                            total_output_tokens += output_tokens
                            
                            # Update model breakdown
                            if model not in model_breakdown:
                                model_breakdown[model] = {
                                    "cost": 0.0,
                                    "input_tokens": 0,
                                    "cache_creation_tokens": 0,
                                    "cache_read_tokens": 0,
                                    "output_tokens": 0,
                                    "requests": 0
                                }
                            
                            model_breakdown[model]["cost"] += item_cost
                            model_breakdown[model]["input_tokens"] += input_tokens
                            model_breakdown[model]["cache_creation_tokens"] += cache_creation_tokens
                            model_breakdown[model]["cache_read_tokens"] += cache_read_tokens
                            model_breakdown[model]["output_tokens"] += output_tokens
                            model_breakdown[model]["requests"] += 1
                            
                            # Track sessions
                            if entry.get('sessionId'):
                                session_count += 1
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in {file_path}: {line[:50]}...")
                        except Exception as e:
                            logger.error(f"Error processing entry: {e}")
                            
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                
        return {
            "total_cost": total_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "model_breakdown": model_breakdown,
            "session_count": session_count,
            "file_count": len(jsonl_files),
            "since_date": since_date.isoformat() if since_date else "all"
        }
    
    async def get_usage_data_async(self, since_date: Optional[datetime] = None, 
                                   progress_callback: Optional[Callable[[str], None]] = None) -> Dict:
        """Async version of get_usage_data that runs in a background thread"""
        loop = asyncio.get_event_loop()
        
        # Create a wrapper that includes progress updates
        def _get_data_with_progress():
            if progress_callback:
                progress_callback("Reading Claude Code usage...")
            result = self.get_usage_data(since_date)
            if progress_callback:
                progress_callback(f"Processed {result['file_count']} files")
            return result
        
        # Run the synchronous method in a thread pool
        return await loop.run_in_executor(self._executor, _get_data_with_progress)
    
    def __del__(self):
        """Clean up the thread pool executor"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)