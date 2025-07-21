"""
Polling engine for LLM Cost Monitor
Manages periodic polling of all configured providers
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from src.core.database import Database
from src.providers.base import ProviderAdapter, ProviderConfig

logger = logging.getLogger(__name__)


class PollingEngine:
    def __init__(self, database: Database):
        self.db = database
        self.providers: Dict[str, ProviderAdapter] = {}
        self.polling_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.poll_interval = 60  # seconds
        
    async def register_provider(self, provider: ProviderAdapter):
        """Register a provider adapter"""
        await provider.initialize()
        self.providers[provider.config.name] = provider
        logger.info(f"Registered provider: {provider.config.name}")
        
    async def unregister_provider(self, name: str):
        """Unregister a provider adapter"""
        if name in self.providers:
            await self.providers[name].cleanup()
            del self.providers[name]
            logger.info(f"Unregistered provider: {name}")
            
    async def start(self):
        """Start the polling engine"""
        if self.is_running:
            return
            
        self.is_running = True
        self.polling_task = asyncio.create_task(self._polling_loop())
        logger.info("Polling engine started")
        
    async def stop(self):
        """Stop the polling engine"""
        self.is_running = False
        
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
                
        # Cleanup all providers
        for provider in self.providers.values():
            await provider.cleanup()
            
        logger.info("Polling engine stopped")
        
    async def _polling_loop(self):
        """Main polling loop"""
        while self.is_running:
            try:
                await self._poll_all_providers()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
                
    async def _poll_all_providers(self):
        """Poll all registered providers"""
        tasks = []
        
        for name, provider in self.providers.items():
            if provider.config.enabled:
                task = asyncio.create_task(self._poll_provider(name, provider))
                tasks.append(task)
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Provider polling error: {result}")
                    
    async def _poll_provider(self, name: str, provider: ProviderAdapter):
        """Poll a single provider and store results"""
        try:
            usage_data = await provider.poll()
            
            if usage_data:
                # Get provider from database
                provider_record = await self.db.get_provider_by_name(name)
                
                if provider_record:
                    # Store usage snapshot
                    await self.db.add_usage_snapshot(
                        provider_id=provider_record['id'],
                        cost=usage_data.total_cost,
                        tokens=usage_data.total_tokens,
                        metadata=usage_data.metadata
                    )
                    
                    logger.debug(f"Stored usage data for {name}: ${usage_data.total_cost:.2f}")
                    
        except Exception as e:
            logger.error(f"Error polling {name}: {e}")
            raise
            
    def get_provider_status(self, name: str) -> Optional[Dict]:
        """Get current status of a provider"""
        provider = self.providers.get(name)
        if not provider:
            return None
            
        return {
            "name": name,
            "enabled": provider.config.enabled,
            "last_poll": provider.get_last_poll_time(),
            "last_data": provider.get_last_data()
        }
        
    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get status of all providers"""
        return {
            name: self.get_provider_status(name)
            for name in self.providers
        }