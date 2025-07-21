"""
OpenRouter provider adapter for LLM Cost Monitor
Handles fetching usage data from OpenRouter API
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from src.providers.base import ProviderAdapter, ProviderConfig, UsageData

logger = logging.getLogger(__name__)


class OpenRouterAdapter(ProviderAdapter):
    """OpenRouter API adapter"""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get OpenRouter authorization headers"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://llm-cost-monitor.app",  # Required by OpenRouter
            "X-Title": "LLM Cost Monitor"  # Optional but recommended
        }
        return headers
        
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenRouter API key"""
        try:
            # OpenRouter provides a key info endpoint
            url = f"{self.BASE_URL}/auth/key"
            response = await self.make_request(url, api_key)
            
            # If we get a response with data, the key is valid
            return "data" in response
            
        except Exception as e:
            logger.error(f"Invalid OpenRouter API key: {e}")
            return False
            
    async def fetch_usage(self) -> UsageData:
        """Fetch usage data from OpenRouter"""
        logger.info(f"Fetching OpenRouter usage data with {len(self.config.api_keys)} API keys")
        
        # For demo purposes, if no real API key, return mock data
        if not self.config.api_keys or self.config.api_keys[0].startswith("sk-or-dummy"):
            logger.info("Using mock data for OpenRouter")
            import random
            mock_cost = random.uniform(5.0, 25.0)
            mock_tokens = random.randint(20000, 60000)
            
            return UsageData(
                timestamp=datetime.utcnow(),
                total_cost=mock_cost,
                total_tokens=mock_tokens,
                model_breakdown={
                    "openai/gpt-4": {"cost": mock_cost * 0.4, "tokens": int(mock_tokens * 0.2)},
                    "anthropic/claude-2": {"cost": mock_cost * 0.3, "tokens": int(mock_tokens * 0.3)},
                    "google/palm-2": {"cost": mock_cost * 0.2, "tokens": int(mock_tokens * 0.3)},
                    "meta-llama/llama-2-70b": {"cost": mock_cost * 0.1, "tokens": int(mock_tokens * 0.2)}
                },
                metadata={"mock": True}
            )
        
        # Initialize totals
        total_cost = 0.0
        total_tokens = 0
        model_breakdown = {}
        
        for api_key in self.config.api_keys:
            try:
                # Get key info which includes usage
                key_url = f"{self.BASE_URL}/auth/key"
                logger.info(f"Requesting OpenRouter key info from: {key_url}")
                
                key_response = await self.make_request(key_url, api_key)
                logger.info(f"OpenRouter key response: {key_response}")
                
                if "data" in key_response:
                    data = key_response["data"]
                    
                    # Get usage from key info
                    usage = data.get("usage", 0.0)
                    limit = data.get("limit", 0.0)
                    limit_remaining = data.get("limit_remaining", 0.0)
                    
                    logger.info(f"OpenRouter usage: ${usage}, limit: ${limit}, remaining: ${limit_remaining}")
                    
                    # The usage field shows total amount spent
                    total_cost = usage
                    
                # Also get credits info
                credits_url = f"{self.BASE_URL}/credits"
                try:
                    credits_response = await self.make_request(credits_url, api_key)
                    logger.info(f"OpenRouter credits response: {credits_response}")
                    
                    if "data" in credits_response:
                        credits_data = credits_response["data"]
                        # Use the usage from credits if available
                        if "total_usage" in credits_data:
                            total_cost = credits_data["total_usage"]
                            
                except Exception as e:
                    logger.warning(f"Could not fetch credits info: {e}")
                    
            except Exception as e:
                logger.error(f"Error fetching OpenRouter usage: {e}")
                # Continue with other API keys
                
        return UsageData(
            timestamp=datetime.utcnow(),
            total_cost=total_cost,
            total_tokens=None,  # OpenRouter doesn't provide aggregate token counts
            model_breakdown=model_breakdown if model_breakdown else None,
            metadata={"provider": "openrouter"}
        )
        
    @staticmethod
    def from_env() -> Optional['OpenRouterAdapter']:
        """Create adapter from environment variables"""
        api_keys = []
        
        # Check for single key
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            api_keys.append(key)
            
        # Check for multiple keys
        i = 1
        while True:
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if not key:
                break
            api_keys.append(key)
            i += 1
            
        if not api_keys:
            return None
            
        config = ProviderConfig(
            name="openrouter",
            display_name="OpenRouter",
            api_keys=api_keys
        )
        
        return OpenRouterAdapter(config)