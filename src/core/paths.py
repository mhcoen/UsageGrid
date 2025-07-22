"""
Path management for UsageGrid application
All user data is stored in ~/.usagegrid
"""
from pathlib import Path
import os
import shutil
import logging
import json
from src.core.default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class UsageGridPaths:
    """Manages all paths for the UsageGrid application"""
    
    @staticmethod
    def get_data_dir() -> Path:
        """Get the main UsageGrid data directory (~/.usagegrid)"""
        data_dir = Path.home() / ".usagegrid"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @staticmethod
    def get_config_path() -> Path:
        """Get the config file path"""
        return UsageGridPaths.get_data_dir() / "config.json"
    
    @staticmethod
    def get_cache_db_path() -> Path:
        """Get the cache database path"""
        return UsageGridPaths.get_data_dir() / "cache.db"
    
    @staticmethod
    def get_logs_dir() -> Path:
        """Get the logs directory"""
        logs_dir = UsageGridPaths.get_data_dir() / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    @staticmethod
    def migrate_from_old_paths():
        """Migrate data from old locations to ~/.usagegrid"""
        data_dir = UsageGridPaths.get_data_dir()
        
        # Migrate config.json from project root
        old_config = Path(__file__).parent.parent.parent / "config.json"
        new_config = UsageGridPaths.get_config_path()
        
        if old_config.exists() and not new_config.exists():
            logger.info(f"Migrating config from {old_config} to {new_config}")
            shutil.copy2(old_config, new_config)
        
        # Migrate cache.db from old data directory
        old_cache_dir = Path(__file__).parent.parent.parent / "data"
        old_cache_db = old_cache_dir / "cache.db"
        new_cache_db = UsageGridPaths.get_cache_db_path()
        
        if old_cache_db.exists() and not new_cache_db.exists():
            logger.info(f"Migrating cache.db from {old_cache_db} to {new_cache_db}")
            shutil.copy2(old_cache_db, new_cache_db)
    
    @staticmethod
    def ensure_default_config():
        """Ensure a default config exists if none is present"""
        config_path = UsageGridPaths.get_config_path()
        
        if not config_path.exists():
            # Create default config with complete settings
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            logger.info(f"Created default config at {config_path}")