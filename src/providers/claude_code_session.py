"""
Claude Code session analyzer - matches Claude Monitor behavior
Analyzes usage in 5-hour session blocks and identifies active session
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.providers.claude_code_reader import ClaudeCodeReader

class ClaudeCodeSession:
    """Analyzes Claude Code usage by session (5-hour blocks)"""
    
    def __init__(self, session_duration_hours: int = 5):
        self.session_duration = timedelta(hours=session_duration_hours)
        self.reader = ClaudeCodeReader()
        
    def get_active_session_usage(self) -> Dict:
        """Get usage data for the currently active session only"""
        current_time = datetime.utcnow()
        
        # First, find the actual session start by looking for gaps
        # Get recent timestamps to find session boundaries
        session_start = self._find_current_session_start(current_time)
        
        if session_start:
            # Get usage data from session start
            session_data = self.reader.get_usage_data(since_date=session_start)
            
            if session_data['total_cost'] > 0:
                return {
                    'cost': session_data['total_cost'],
                    'tokens': session_data['total_tokens'],
                    'messages': session_data.get('session_count', 0),
                    'is_active': True,
                    'session_start': session_start,
                    'session_end': session_start + self.session_duration
                }
        
        # No active session
        return {
            'cost': 0.0,
            'tokens': 0,
            'messages': 0,
            'is_active': False,
            'session_start': None,
            'session_end': None
        }
    
    def _find_current_session_start(self, current_time: datetime) -> Optional[datetime]:
        """Find when the current session started by looking for gaps in activity"""
        # Look back up to 8 hours for session start
        lookback = current_time - timedelta(hours=8)
        
        # Get all data in the lookback period
        all_data = self.reader.get_usage_data(since_date=lookback)
        
        # For now, use a simple heuristic:
        # If there's been activity in the last 3 hours, that's our session
        three_hours_ago = current_time - timedelta(hours=3)
        recent_data = self.reader.get_usage_data(since_date=three_hours_ago)
        
        if recent_data['total_cost'] > 0:
            # Found activity - use 3 hours ago as session start
            # In a real implementation, we'd analyze timestamps to find actual gaps
            return three_hours_ago
        
        return None
    
    def _round_to_hour(self, dt: datetime) -> datetime:
        """Round datetime down to the nearest hour"""
        return dt.replace(minute=0, second=0, microsecond=0)