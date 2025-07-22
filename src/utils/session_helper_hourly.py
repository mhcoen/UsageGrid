"""
Helper to calculate Claude Code session boundaries using hourly alignment
Claude Code sessions start on the hour and last for 5 hours
"""
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def find_session_start_hourly(now: datetime) -> datetime:
    """
    Find when the current session started using hourly boundaries.
    
    Claude Code sessions:
    - Start on the hour (e.g., 9:00 PM, 2:00 AM, 7:00 AM, etc.)
    - Last for exactly 5 hours
    - Reset automatically at the next hourly boundary after expiration
    
    Args:
        now: Current datetime (timezone-aware or naive)
        
    Returns:
        datetime: Start of the current session (on the hour)
    """
    # Remove timezone info for calculation
    if hasattr(now, 'tzinfo') and now.tzinfo:
        now = now.replace(tzinfo=None)
    
    # Find the current hour
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    
    # Sessions start every 5 hours, so find which 5-hour block we're in
    # Calculate hours since midnight
    hours_since_midnight = current_hour.hour
    
    # Find the session start within today
    # Sessions could start at: 0, 5, 10, 15, 20 (and roll over)
    session_start_hour = (hours_since_midnight // 5) * 5
    
    # Create the session start time
    session_start = current_hour.replace(hour=session_start_hour)
    
    # Check if we're still in this session
    session_end = session_start + timedelta(hours=5)
    
    if now >= session_end:
        # We've passed this session, move to the next one
        session_start = session_end
        
    logger.debug(f"Current time: {now}, Session start: {session_start}, Session end: {session_start + timedelta(hours=5)}")
    
    return session_start

def get_next_session_start(now: datetime) -> datetime:
    """
    Get when the next session will start.
    
    Args:
        now: Current datetime
        
    Returns:
        datetime: Start of the next session (on the hour)
    """
    current_session = find_session_start_hourly(now)
    next_session = current_session + timedelta(hours=5)
    return next_session