"""
Database module for LLM Cost Monitor
Handles all SQLite operations for storing provider data and usage history
"""
import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = Path.home() / ".llm-cost-monitor" / "data.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        
    async def initialize(self):
        """Initialize database and create tables"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row  # Enable row factory for dict-like access
        await self._create_tables()
        
    async def _create_tables(self):
        """Create database tables"""
        await self.conn.executescript("""
            -- Providers table
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                color TEXT,
                config JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- API Keys table
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                key_hash TEXT NOT NULL,
                nickname TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );
            
            -- Usage snapshots table
            CREATE TABLE IF NOT EXISTS usage_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                provider_id INTEGER NOT NULL,
                api_key_id INTEGER,
                cost REAL NOT NULL,
                tokens_used INTEGER,
                model TEXT,
                metadata JSON,
                FOREIGN KEY (provider_id) REFERENCES providers(id),
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            );
            
            -- Daily summaries table
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                provider_id INTEGER NOT NULL,
                total_cost REAL NOT NULL,
                total_tokens INTEGER,
                request_count INTEGER,
                models_used JSON,
                UNIQUE(date, provider_id),
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
                ON usage_snapshots(timestamp);
            CREATE INDEX IF NOT EXISTS idx_usage_provider 
                ON usage_snapshots(provider_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_daily_date 
                ON daily_summaries(date, provider_id);
        """)
        await self.conn.commit()
        
        # Insert default providers
        await self._insert_default_providers()
        
    async def _insert_default_providers(self):
        """Insert default provider configurations"""
        providers = [
            ("openai", "OpenAI", "#10a37f"),
            ("anthropic", "Anthropic", "#e16e3d"),
            ("openrouter", "OpenRouter", "#8b5cf6"),
            ("huggingface", "HuggingFace", "#ffbe0b")
        ]
        
        for name, display_name, color in providers:
            await self.conn.execute(
                """INSERT OR IGNORE INTO providers (name, display_name, color) 
                   VALUES (?, ?, ?)""",
                (name, display_name, color)
            )
        await self.conn.commit()
        
    async def add_usage_snapshot(self, provider_id: int, cost: float, 
                                tokens: Optional[int] = None, 
                                model: Optional[str] = None,
                                api_key_id: Optional[int] = None,
                                metadata: Optional[Dict] = None):
        """Add a usage snapshot"""
        await self.conn.execute(
            """INSERT INTO usage_snapshots 
               (timestamp, provider_id, api_key_id, cost, tokens_used, model, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.utcnow(), provider_id, api_key_id, cost, tokens, model,
             json.dumps(metadata) if metadata else None)
        )
        await self.conn.commit()
        
    async def get_provider_by_name(self, name: str) -> Optional[Dict]:
        """Get provider by name"""
        async with self.conn.execute(
            "SELECT * FROM providers WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {key: row[key] for key in row.keys()}
        return None
        
    async def get_all_providers(self) -> List[Dict]:
        """Get all providers"""
        async with self.conn.execute("SELECT * FROM providers") as cursor:
            rows = await cursor.fetchall()
            return [{key: row[key] for key in row.keys()} for row in rows]
            
    async def get_recent_usage(self, provider_id: int, hours: int = 24) -> List[Dict]:
        """Get recent usage data for a provider"""
        query = """
            SELECT * FROM usage_snapshots 
            WHERE provider_id = ? 
                AND timestamp > datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC
        """
        async with self.conn.execute(query, (provider_id, hours)) as cursor:
            rows = await cursor.fetchall()
            return [{key: row[key] for key in row.keys()} for row in rows]
            
    async def get_daily_summary(self, provider_id: int, days: int = 30) -> List[Dict]:
        """Get daily summary for a provider"""
        query = """
            SELECT * FROM daily_summaries 
            WHERE provider_id = ? 
                AND date > date('now', '-' || ? || ' days')
            ORDER BY date DESC
        """
        async with self.conn.execute(query, (provider_id, days)) as cursor:
            rows = await cursor.fetchall()
            return [{key: row[key] for key in row.keys()} for row in rows]
            
    async def update_daily_summary(self, provider_id: int, date: str, 
                                  cost: float, tokens: int, requests: int,
                                  models: List[str]):
        """Update or insert daily summary"""
        await self.conn.execute(
            """INSERT OR REPLACE INTO daily_summaries 
               (date, provider_id, total_cost, total_tokens, request_count, models_used)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (date, provider_id, cost, tokens, requests, json.dumps(models))
        )
        await self.conn.commit()
        
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()