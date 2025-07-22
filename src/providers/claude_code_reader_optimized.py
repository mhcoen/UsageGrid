"""
Optimized Claude Code usage reader that efficiently tracks multiple active sessions
"""
import json
import logging
import glob
import os
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)

@dataclass
class FileTracker:
    """Track file state for efficient reading"""
    path: str
    last_modified: float
    last_position: int
    last_read_time: float
    session_start: Optional[datetime] = None
    
class ClaudeCodeReaderOptimized:
    """Optimized reader for Claude Code JSONL files with caching and incremental reading"""
    
    # Pricing per million tokens
    MODEL_PRICING = {
        "claude-3-opus": {
            "input": 15.0, 
            "output": 75.0,
            "cache_creation": 18.75,
            "cache_read": 1.5
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
        
        # File tracking for optimization
        self.file_trackers: Dict[str, FileTracker] = {}
        self.tracker_lock = threading.Lock()
        
        # Cache for session data
        self.session_cache: Dict[str, Dict] = {}
        self.cache_lock = threading.Lock()
        
        # Processed entry IDs to avoid duplicates
        self.processed_ids: Set[str] = set()
        
        # Session window (5 hours + 30 min buffer)
        self.session_window_hours = 5.5
        
        # Accumulated totals for each time window
        self.accumulated_totals: Dict[str, Dict] = {}
        
    def get_active_session_files(self) -> List[FileTracker]:
        """Get only files that might contain active session data"""
        cutoff_time = time.time() - (self.session_window_hours * 3600)
        active_files = []
        
        # Find all JSONL files
        pattern = str(self.claude_dir / "**" / "*.jsonl")
        
        for file_path in glob.glob(pattern, recursive=True):
            try:
                stat = os.stat(file_path)
                
                # Skip empty files
                if stat.st_size == 0:
                    continue
                    
                # Only consider files modified within session window
                if stat.st_mtime > cutoff_time:
                    with self.tracker_lock:
                        if file_path not in self.file_trackers:
                            self.file_trackers[file_path] = FileTracker(
                                path=file_path,
                                last_modified=0,
                                last_position=0,
                                last_read_time=0
                            )
                    active_files.append(self.file_trackers[file_path])
                    
            except OSError:
                continue
                
        return active_files
        
    def read_new_entries(self, tracker: FileTracker, since_date: Optional[datetime] = None) -> List[Dict]:
        """Read only new entries from a file since last check"""
        new_entries = []
        
        try:
            stat = os.stat(tracker.path)
            
            # Check if file has been modified
            if stat.st_mtime <= tracker.last_modified and tracker.last_position > 0:
                return new_entries  # No new data
                
            with open(tracker.path, 'r') as f:
                # Seek to last read position
                if tracker.last_position > 0:
                    f.seek(tracker.last_position)
                    
                current_position = f.tell()
                
                for line in f:
                    if not line.strip():
                        continue
                        
                    try:
                        entry = json.loads(line)
                        
                        # Check timestamp
                        if since_date is not None:
                            timestamp_str = entry.get('timestamp')
                            if timestamp_str:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if timestamp.tzinfo:
                                    timestamp = timestamp.replace(tzinfo=None)
                                if timestamp < since_date:
                                    continue
                                    
                        # Deduplicate
                        message_id = entry.get('message_id') or entry.get('message', {}).get('id', '')
                        request_id = entry.get('requestId') or entry.get('request_id', '')
                        
                        if message_id and request_id:
                            entry_id = f"{message_id}:{request_id}"
                            if entry_id in self.processed_ids:
                                continue
                            self.processed_ids.add(entry_id)
                            
                        new_entries.append(entry)
                        
                    except json.JSONDecodeError:
                        continue
                        
                # Update tracker
                tracker.last_position = f.tell()
                tracker.last_modified = stat.st_mtime
                tracker.last_read_time = time.time()
                
        except Exception as e:
            logger.error(f"Error reading file {tracker.path}: {e}")
            
        return new_entries
        
    def calculate_entry_cost(self, entry: Dict) -> Tuple[float, int, int, str]:
        """Calculate cost for a single entry"""
        message = entry.get('message', {})
        usage = message.get('usage', {})
        
        if not usage:
            return 0.0, 0, 0, ""
            
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        cache_creation_tokens = usage.get('cache_creation_tokens', 0)
        cache_read_tokens = usage.get('cache_read_tokens', 0)
        
        # Non-cache tokens for display
        non_cache_input = input_tokens
        non_cache_output = output_tokens
        
        model = message.get('model', 'claude-3.5-sonnet')
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING['default'])
        
        # Calculate costs
        input_cost = (non_cache_input / 1_000_000) * pricing['input']
        output_cost = (non_cache_output / 1_000_000) * pricing['output']
        cache_creation_cost = (cache_creation_tokens / 1_000_000) * pricing['cache_creation']
        cache_read_cost = (cache_read_tokens / 1_000_000) * pricing['cache_read']
        
        total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost
        
        return total_cost, non_cache_input, non_cache_output, model
        
    def get_usage_data(self, since_date: Optional[datetime] = None) -> Dict:
        """Get usage data efficiently by only reading new entries"""
        active_files = self.get_active_session_files()
        logger.info(f"Found {len(active_files)} active session files")
        
        # Get cache key for this time window
        cache_key = f"{since_date.isoformat()}" if since_date else "all"
        
        # Get accumulated totals for this time window
        if cache_key in self.accumulated_totals:
            total_cost = self.accumulated_totals[cache_key].get('cost', 0.0)
            total_input_tokens = self.accumulated_totals[cache_key].get('input_tokens', 0)
            total_output_tokens = self.accumulated_totals[cache_key].get('output_tokens', 0)
            model_breakdown = self.accumulated_totals[cache_key].get('model_breakdown', {})
        else:
            total_cost = 0.0
            total_input_tokens = 0
            total_output_tokens = 0
            model_breakdown = {}
        
        # Process each active file for NEW entries only
        new_entries_count = 0
        for tracker in active_files:
            new_entries = self.read_new_entries(tracker, since_date)
            new_entries_count += len(new_entries)
            
            for entry in new_entries:
                cost, input_tokens, output_tokens, model = self.calculate_entry_cost(entry)
                
                if cost > 0:
                    total_cost += cost
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
                    
                    # Update model breakdown
                    if model:
                        if model not in model_breakdown:
                            model_breakdown[model] = {
                                'cost': 0.0,
                                'input_tokens': 0,
                                'output_tokens': 0,
                                'count': 0
                            }
                        model_breakdown[model]['cost'] += cost
                        model_breakdown[model]['input_tokens'] += input_tokens
                        model_breakdown[model]['output_tokens'] += output_tokens
                        model_breakdown[model]['count'] += 1
                        
        # Update accumulated totals
        self.accumulated_totals[cache_key] = {
            'cost': total_cost,
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'model_breakdown': model_breakdown.copy()
        }
        
        logger.info(f"Processed {new_entries_count} new entries, total tokens: {total_input_tokens + total_output_tokens}")
                    
        return {
            'total_cost': total_cost,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'model_breakdown': model_breakdown,
            'files_checked': len(active_files),
            'optimization_stats': {
                'files_tracked': len(self.file_trackers),
                'entries_cached': len(self.processed_ids),
                'active_files': len(active_files)
            }
        }
        
    def get_token_rate_history(self, session_start: datetime, interval_minutes: int = 5) -> List[int]:
        """Calculate token usage rates from session history"""
        rates = []
        entries_with_time = []
        
        active_files = self.get_active_session_files()
        
        # For rate history, we need to read ALL entries in the session, not just new ones
        for tracker in active_files:
            try:
                with open(tracker.path, 'r') as f:
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
                                    
                                # Only include entries within session
                                if timestamp < session_start:
                                    continue
                                    
                                message = entry.get('message', {})
                                usage = message.get('usage', {})
                                
                                if usage:
                                    tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                                    if tokens > 0:
                                        entries_with_time.append((timestamp, tokens))
                                        
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading rate history from {tracker.path}: {e}")
                continue
                            
        # Sort by timestamp
        entries_with_time.sort(key=lambda x: x[0])
        
        if not entries_with_time:
            return rates
            
        # Calculate rates
        current_time = session_start
        session_end = session_start + timedelta(hours=5)
        
        while current_time < min(datetime.now().replace(tzinfo=None), session_end):
            interval_end = current_time + timedelta(minutes=interval_minutes)
            interval_tokens = sum(tokens for ts, tokens in entries_with_time 
                                if current_time <= ts < interval_end)
            rates.append(interval_tokens)
            current_time = interval_end
            
        return rates
        
    def clear_old_cache(self):
        """Clear old cached data outside session window"""
        cutoff_time = time.time() - (self.session_window_hours * 3600)
        
        with self.tracker_lock:
            # Remove old file trackers
            old_trackers = [path for path, tracker in self.file_trackers.items()
                           if tracker.last_read_time < cutoff_time]
            for path in old_trackers:
                del self.file_trackers[path]
                
        # Clear old processed IDs periodically (keep last 10k)
        if len(self.processed_ids) > 10000:
            self.processed_ids = set(list(self.processed_ids)[-5000:])
            
        logger.info(f"Cache cleanup: {len(self.file_trackers)} active files, "
                   f"{len(self.processed_ids)} cached entries")