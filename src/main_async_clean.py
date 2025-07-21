#!/usr/bin/env python3
"""
LLM Cost Monitor - Clean async implementation
"""
import sys
import asyncio
import signal
import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication
from src.ui.async_main_window import AsyncMainWindow
from src.core.polling_engine import PollingEngine
from src.core.database import Database
from src.providers.openai_adapter import OpenAIAdapter
from src.providers.anthropic_adapter import AnthropicAdapter
from src.providers.openrouter_adapter import OpenRouterAdapter
from src.providers.huggingface_adapter import HuggingFaceAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncLLMMonitor:
    """Main application class with clean async separation"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("LLM Cost Monitor")
        self.app.setOrganizationName("LLMCostMonitor")
        
        self.db: Optional[Database] = None
        self.polling_engine: Optional[PollingEngine] = None
        self.main_window: Optional[AsyncMainWindow] = None
        
    async def initialize_backend(self):
        """Initialize backend components"""
        try:
            # Initialize database
            self.db = Database()
            await self.db.initialize()
            logger.info("Database initialized")
            
            # Initialize polling engine
            self.polling_engine = PollingEngine(self.db)
            
            # Register providers
            await self._register_providers()
            
            # Start polling engine
            await self.polling_engine.start()
            logger.info("Polling engine started")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            return False
            
    async def _register_providers(self):
        """Register available providers"""
        # OpenAI
        openai = OpenAIAdapter.from_env()
        if openai:
            await self.polling_engine.register_provider(openai)
            logger.info("Registered OpenAI provider")
        else:
            logger.warning("No OpenAI API key found")
            
        # Anthropic
        anthropic = AnthropicAdapter.from_env()
        if anthropic:
            await self.polling_engine.register_provider(anthropic)
            logger.info("Registered Anthropic provider")
        else:
            logger.warning("No Anthropic API key found")
            
        # OpenRouter
        openrouter = OpenRouterAdapter.from_env()
        if openrouter:
            await self.polling_engine.register_provider(openrouter)
            logger.info("Registered OpenRouter provider")
        else:
            logger.warning("No OpenRouter API key found")
            
        # HuggingFace
        huggingface = HuggingFaceAdapter.from_env()
        if huggingface:
            await self.polling_engine.register_provider(huggingface)
            logger.info("Registered HuggingFace provider")
        else:
            logger.warning("No HuggingFace API token found")
        
    async def get_providers(self):
        """Get all providers from database"""
        return await self.db.get_all_providers()
        
    async def cleanup_backend(self):
        """Cleanup backend components"""
        if self.polling_engine:
            await self.polling_engine.stop()
            logger.info("Polling engine stopped")
            
        if self.db:
            await self.db.close()
            logger.info("Database closed")
            
    def create_ui(self):
        """Create UI components"""
        self.main_window = AsyncMainWindow(self.db, self.polling_engine)
        return self.main_window
        
    def run(self):
        """Run the application"""
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Run backend initialization in a separate event loop
        init_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(init_loop)
        
        try:
            # Initialize backend
            success = init_loop.run_until_complete(self.initialize_backend())
            if not success:
                logger.error("Backend initialization failed")
                return 1
                
            # Get providers
            providers = init_loop.run_until_complete(self.get_providers())
            
        finally:
            init_loop.close()
            
        # Create UI in main thread
        window = self.create_ui()
        
        # Add provider cards
        for provider in providers:
            if provider['name'] in self.polling_engine.providers:
                window.add_provider_card(
                    provider['name'],
                    provider['display_name'],
                    provider['color']
                )
                
        # Start async polling
        window.start_async_polling()
        
        # Show window
        window.show()
        
        # Run Qt event loop
        exit_code = self.app.exec()
        
        # Cleanup
        cleanup_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cleanup_loop)
        
        try:
            cleanup_loop.run_until_complete(self.cleanup_backend())
        finally:
            cleanup_loop.close()
            
        return exit_code


def main():
    """Main entry point"""
    monitor = AsyncLLMMonitor()
    sys.exit(monitor.run())


if __name__ == "__main__":
    main()