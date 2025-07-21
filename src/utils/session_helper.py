"""
Helper to calculate Claude Code session boundaries

Each project has one JSONL file containing all sessions.
Sessions are 5-hour windows starting from the first message after a gap.
"""
from datetime import datetime, timedelta
import json
import glob
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def find_session_start(now: datetime, claude_dir: Path = None) -> datetime:
    """
    Find when the current session started by analyzing timestamps in JSONL files.
    
    Sessions are 5-hour windows. A new session starts when:
    1. It's the first message ever, OR
    2. The previous session (5 hours from its start) has expired
    
    Args:
        now: Current datetime
        claude_dir: Path to Claude projects directory
        
    Returns:
        datetime: Start of the current session
    """
    if claude_dir is None:
        claude_dir = Path.home() / ".claude" / "projects"
    
    # Find all JSONL files
    pattern = str(claude_dir / "**" / "*.jsonl")
    jsonl_files = glob.glob(pattern, recursive=True)
    
    all_timestamps = []
    
    # Collect all timestamps from all files
    for jsonl_path in jsonl_files:
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                        if 'timestamp' in obj:
                            timestamp = datetime.fromisoformat(obj['timestamp'].rstrip('Z'))
                            all_timestamps.append(timestamp)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            logger.warning(f"Error reading {jsonl_path}: {e}")
            continue
    
    if not all_timestamps:
        # No messages found
        return now
    
    # Sort timestamps chronologically
    all_timestamps.sort()
    
    # Find session starts by looking for gaps
    session_starts = []
    
    for i, timestamp in enumerate(all_timestamps):
        if i == 0:
            # First message ever starts a session
            session_starts.append(timestamp)
        else:
            # Check if this message is in the previous session
            # Find the most recent session start before this timestamp
            prev_session_start = None
            for session_start in reversed(session_starts):
                if session_start <= timestamp:
                    prev_session_start = session_start
                    break
            
            if prev_session_start:
                # Check if previous session has expired
                prev_session_end = prev_session_start + timedelta(hours=5)
                if timestamp > prev_session_end:
                    # This message starts a new session
                    session_starts.append(timestamp)
            else:
                # Shouldn't happen, but handle it
                session_starts.append(timestamp)
    
    # Find the current active session
    current_session_start = None
    for session_start in reversed(session_starts):
        session_end = session_start + timedelta(hours=5)
        if session_start <= now <= session_end:
            current_session_start = session_start
            break
    
    if current_session_start is None:
        # No active session - next message will start a new one
        logger.info("No active session found")
        return now
    
    return current_session_start