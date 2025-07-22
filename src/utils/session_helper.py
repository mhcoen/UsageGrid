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

# Cache for session start time to avoid repeated file scanning
_session_cache = {
    'session_start': None,
    'session_end': None,
    'last_check': None
}

def find_session_start(now: datetime, claude_dir: Path = None) -> datetime:
    """
    Find when the current session started by analyzing timestamps in JSONL files.
    
    Sessions are 5-hour windows. A new session starts when:
    1. It's the first message ever, OR
    2. The previous session (5 hours from its start) has expired
    
    NOTE: Claude Code Monitor shows sessions ending on specific times (e.g., 9:00 PM),
    so we need to align our calculations with what the monitor shows.
    
    Args:
        now: Current datetime
        claude_dir: Path to Claude projects directory
        
    Returns:
        datetime: Start of the current session
    """
    global _session_cache
    
    # Check if we have a valid cached session
    if (_session_cache['session_start'] and 
        _session_cache['session_end'] and 
        _session_cache['last_check']):
        # If we're still in the cached session window, return cached value
        if _session_cache['session_start'] <= now <= _session_cache['session_end']:
            # Session is still valid, no need to rescan
            return _session_cache['session_start']
        # If session has expired, we need to find the new session
        # But only check once per minute to avoid excessive scanning
        elif (now - _session_cache['last_check']).total_seconds() < 60:
            # Return the expired session start for now
            return _session_cache['session_start']
    
    # Update last check time
    _session_cache['last_check'] = now
    
    if claude_dir is None:
        claude_dir = Path.home() / ".claude" / "projects"
    
    # Find all JSONL files and filter to only recent ones
    pattern = str(claude_dir / "**" / "*.jsonl")
    all_jsonl_files = glob.glob(pattern, recursive=True)
    
    # Only check files modified in the last 24 hours to speed up search
    recent_files = []
    cutoff_time = (now - timedelta(hours=24)).timestamp()
    
    for jsonl_path in all_jsonl_files:
        try:
            mtime = os.path.getmtime(jsonl_path)
            if mtime > cutoff_time:
                recent_files.append(jsonl_path)
        except:
            continue
    
    jsonl_files = recent_files
    logger.info(f"Checking {len(jsonl_files)} recent JSONL files (out of {len(all_jsonl_files)} total)")
    
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
    
    # Find session starts
    # Sessions start on the hour and last 5 hours
    session_starts = []
    
    for timestamp in all_timestamps:
        # Round this timestamp down to the hour
        hour_aligned = timestamp.replace(minute=0, second=0, microsecond=0)
        
        # Check if this timestamp fits in any existing session
        fits_in_existing = False
        for session_start in session_starts:
            session_end = session_start + timedelta(hours=5)
            if session_start <= hour_aligned < session_end:
                fits_in_existing = True
                break
        
        # If it doesn't fit in any existing session, it starts a new one
        if not fits_in_existing:
            session_starts.append(hour_aligned)
    
    # Sort session starts
    session_starts.sort()
    
    # Find the current active session
    current_session_start = None
    for session_start in reversed(session_starts):
        session_end = session_start + timedelta(hours=5)
        if session_start <= now <= session_end:
            current_session_start = session_start
            # Cache the session info
            _session_cache['session_start'] = session_start
            _session_cache['session_end'] = session_end
            # Found active session
            break
    
    if current_session_start is None:
        # No active session - next message will start a new one
        logger.info("No active session found")
        # Clear cache since there's no active session
        _session_cache['session_start'] = None
        _session_cache['session_end'] = None
        # Return current time rounded down to hour (would be start of new session)
        return now.replace(minute=0, second=0, microsecond=0)
    
    return current_session_start