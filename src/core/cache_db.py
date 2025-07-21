"""
Simple SQLite cache for provider historical data
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CacheDB:
    """Simple cache database for historical provider data"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use user's home directory
            cache_dir = Path.home() / ".llm_cost_monitor"
            cache_dir.mkdir(exist_ok=True)
            db_path = cache_dir / "cache.db"
            
        self.db_path = str(db_path)
        self._init_db()
        
    def _init_db(self):
        """Initialize the database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS openai_daily_usage (
                    date TEXT PRIMARY KEY,
                    tokens INTEGER,
                    cost REAL,
                    last_updated TIMESTAMP,
                    raw_data TEXT
                )
            """)
            conn.commit()
            
    def get_openai_daily_usage(self, date: str) -> Optional[Dict]:
        """Get cached OpenAI usage for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT tokens, cost, raw_data FROM openai_daily_usage WHERE date = ?",
                (date,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "tokens": row[0],
                    "cost": row[1],
                    "raw_data": json.loads(row[2]) if row[2] else None
                }
            return None
            
    def set_openai_daily_usage(self, date: str, tokens: int, cost: float, raw_data: Optional[dict] = None):
        """Cache OpenAI usage for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO openai_daily_usage 
                (date, tokens, cost, last_updated, raw_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                date,
                tokens,
                cost,
                datetime.now().isoformat(),
                json.dumps(raw_data) if raw_data else None
            ))
            conn.commit()
            
    def get_openai_weekly_usage(self, end_date: datetime) -> Dict[str, Dict]:
        """Get cached weekly usage data"""
        weekly_data = {}
        
        # Get data for the past 7 days
        for i in range(7):
            date = end_date - timedelta(days=i)
            date_str = date.date().isoformat()
            
            cached = self.get_openai_daily_usage(date_str)
            if cached:
                weekly_data[date_str] = {
                    "tokens": cached["tokens"],
                    "cost": cached["cost"]
                }
                
        return weekly_data
        
    def should_refresh_date(self, date: str) -> bool:
        """Check if we should refresh data for a given date"""
        # Don't refresh if it's not today's date and we have data
        today = datetime.now().date().isoformat()
        
        if date != today:
            # For historical dates, if we have any data, don't refresh
            cached = self.get_openai_daily_usage(date)
            return cached is None
            
        # For today, always refresh to get latest data
        return True