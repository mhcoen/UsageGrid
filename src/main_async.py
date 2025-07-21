#!/usr/bin/env python3
"""
LLM Cost Monitor - Async version with proper event loop integration
"""
import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
import signal
import logging

from src.ui.main_window import MainWindow
from src.core.polling_engine import PollingEngine
from src.core.database import Database
from src.providers.openai_adapter import OpenAIAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncBridge(QObject):
    """Bridge between async operations and Qt signals"""
    update_ui = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.loop = None
        self.thread = None
        
    def start_async_loop(self):
        """Start async event loop in separate thread"""
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def _run_loop(self):
        """Run the async event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def run_coroutine(self, coro):
        """Schedule a coroutine on the async loop"""
        if self.loop and self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            return future
        else:
            raise RuntimeError("Async loop not running")
            
    def stop(self):
        """Stop the async loop"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            if self.thread:
                self.thread.join(timeout=2.0)


class AsyncApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("LLM Cost Monitor")
        self.app.setOrganizationName("LLMCostMonitor")
        
        # Initialize components
        self.db = None
        self.polling_engine = None
        self.main_window = None
        self.bridge = AsyncBridge()
        self.update_timer = None
        
    async def initialize(self):
        """Initialize application components"""
        try:
            # Initialize database
            self.db = Database()
            await self.db.initialize()
            
            # Initialize polling engine
            self.polling_engine = PollingEngine(self.db)
            
            # Register providers
            await self._register_providers()
            
            # Start polling
            await self.polling_engine.start()
            
            logger.info("Async components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize async components: {e}")
            raise
            
    async def _register_providers(self):
        """Register available providers"""
        # OpenAI
        openai = OpenAIAdapter.from_env()
        if openai:
            await self.polling_engine.register_provider(openai)
            logger.info("Registered OpenAI provider")
        else:
            logger.warning("No OpenAI API key found in environment")
            
    def create_ui(self):
        """Create UI components in main thread"""
        # Create main window
        self.main_window = MainWindow(self.db, self.polling_engine)
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # Update every second
        
        # Show window
        self.main_window.show()
        
    async def get_providers(self):
        """Get provider list"""
        return await self.db.get_all_providers()
        
    def update_ui(self):
        """Update UI with latest data from async components"""
        if self.polling_engine:
            # Get data in thread-safe way
            future = self.bridge.run_coroutine(self._get_ui_data())
            # We'll just log for now since we can't block
            future.add_done_callback(self._handle_ui_data)
            
    async def _get_ui_data(self):
        """Get data for UI update"""
        statuses = self.polling_engine.get_all_statuses()
        providers = await self.db.get_all_providers()
        return {"statuses": statuses, "providers": providers}
        
    def _handle_ui_data(self, future):
        """Handle UI data callback"""
        try:
            data = future.result()
            # Update UI in main thread
            if self.main_window:
                statuses = data["statuses"]
                total_cost = 0.0
                
                for name, status in statuses.items():
                    if name in self.main_window.provider_cards and status:
                        card = self.main_window.provider_cards[name]
                        
                        if status['last_data']:
                            cost = status['last_data'].total_cost
                            card.update_data(cost, "Active")
                            total_cost += cost
                        else:
                            card.update_data(0.0, "Waiting...")
                            
                self.main_window.total_label.setText(f"Total: ${total_cost:.2f}")
                
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            
    async def cleanup(self):
        """Cleanup application resources"""
        if self.polling_engine:
            await self.polling_engine.stop()
        if self.db:
            await self.db.close()
            
    def run(self):
        """Run the application"""
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Start async bridge
        self.bridge.start_async_loop()
        
        # Initialize async components
        future = self.bridge.run_coroutine(self.initialize())
        future.result()  # Wait for initialization
        
        # Get providers
        future = self.bridge.run_coroutine(self.get_providers())
        providers = future.result()
        
        # Create UI in main thread
        self.create_ui()
        
        # Add provider cards
        for provider in providers:
            if provider['name'] in self.polling_engine.providers:
                self.main_window.add_provider_card(
                    provider['name'],
                    provider['display_name'],
                    provider['color']
                )
        
        try:
            # Run Qt event loop
            exit_code = self.app.exec()
        finally:
            # Cleanup
            if self.update_timer:
                self.update_timer.stop()
            
            cleanup_future = self.bridge.run_coroutine(self.cleanup())
            cleanup_future.result(timeout=5.0)
            
            self.bridge.stop()
            
        return exit_code


def main():
    """Main entry point"""
    app = AsyncApplication()
    sys.exit(app.run())


if __name__ == "__main__":
    main()