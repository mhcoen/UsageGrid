"""
OpenAI provider adapter for LLM Cost Monitor
Handles fetching usage data from OpenAI API
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.providers.base import ProviderAdapter, ProviderConfig, UsageData

logger = logging.getLogger(__name__)


class OpenAIAdapter(ProviderAdapter):
    """OpenAI API adapter"""
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.org_id = None  # Will be fetched if needed
        
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get OpenAI authorization headers"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Add organization if specified
        org_id = os.getenv("OPENAI_ORG_ID")
        if org_id:
            headers["OpenAI-Organization"] = org_id
            
        return headers
        
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenAI API key"""
        try:
            # Try to fetch models as a validation check
            url = f"{self.BASE_URL}/models"
            await self.make_request(url, api_key)
            return True
        except Exception as e:
            logger.error(f"Invalid OpenAI API key: {e}")
            return False
            
    async def fetch_usage(self) -> UsageData:
        """Fetch usage data from OpenAI"""
        logger.info(f"Fetching OpenAI usage data with {len(self.config.api_keys)} API keys")
        
        # Get the date range for today
        today = datetime.utcnow().date()
        start_date = today.isoformat()
        end_date = (today + timedelta(days=1)).isoformat()
        
        # Initialize totals
        total_cost = 0.0
        total_tokens = 0
        model_breakdown = {}
        
        # For demo purposes, if no real API key, return mock data
        if not self.config.api_keys or self.config.api_keys[0].startswith("sk-dummy"):
            logger.info("Using mock data for OpenAI")
            import random
            mock_cost = random.uniform(10.0, 50.0)
            mock_tokens = random.randint(10000, 100000)
            
            return UsageData(
                timestamp=datetime.utcnow(),
                total_cost=mock_cost,
                total_tokens=mock_tokens,
                model_breakdown={
                    "gpt-4": {"cost": mock_cost * 0.7, "tokens": int(mock_tokens * 0.7)},
                    "gpt-3.5-turbo": {"cost": mock_cost * 0.3, "tokens": int(mock_tokens * 0.3)}
                },
                metadata={"mock": True, "date": start_date}
            )
        
        # Fetch usage for each API key
        for api_key in self.config.api_keys:
            try:
                # OpenAI usage endpoint requires a date parameter
                # Note: This endpoint may require additional permissions
                url = f"{self.BASE_URL}/usage"
                params = {
                    "date": start_date  # YYYY-MM-DD format
                }
                
                logger.info(f"Requesting OpenAI usage from: {url} with date: {start_date}")
                
                try:
                    response = await self.make_request(
                        url, api_key, 
                        params=params
                    )
                    
                    logger.info(f"OpenAI response: {response}")
                    
                    # The actual response structure needs to be determined
                    # For now, log the response to understand the format
                    
                except Exception as e:
                    if "insufficient permissions" in str(e):
                        logger.warning("OpenAI API key lacks organization.read scope")
                    else:
                        logger.error(f"OpenAI usage request failed: {e}")
                    raise
                
                # Parse response - OpenAI returns token counts, not costs
                if "data" in response:
                    for item in response["data"]:
                        context_tokens = item.get("n_context_tokens_total", 0)
                        generated_tokens = item.get("n_generated_tokens_total", 0)
                        total_item_tokens = context_tokens + generated_tokens
                        model = item.get("snapshot_id", "unknown")
                        
                        # Calculate cost based on model pricing
                        # Prices per 1M tokens (as of 2024)
                        model_pricing = {
                            "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},  # per 1M tokens
                            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
                            "gpt-4": {"input": 30.0, "output": 60.0},
                            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
                            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
                        }
                        
                        # Get pricing for this model (default to gpt-4o-mini pricing)
                        pricing = model_pricing.get(model, model_pricing["gpt-4o-mini"])
                        
                        # Calculate cost
                        input_cost = (context_tokens / 1_000_000) * pricing["input"]
                        output_cost = (generated_tokens / 1_000_000) * pricing["output"]
                        item_cost = input_cost + output_cost
                        
                        total_cost += item_cost
                        total_tokens += total_item_tokens
                        
                        if model not in model_breakdown:
                            model_breakdown[model] = {"cost": 0.0, "tokens": 0}
                        
                        model_breakdown[model]["cost"] += item_cost
                        model_breakdown[model]["tokens"] += total_item_tokens
                        
            except Exception as e:
                logger.error(f"Error fetching OpenAI usage: {e}")
                # Continue with other API keys
                
        return UsageData(
            timestamp=datetime.utcnow(),
            total_cost=total_cost,
            total_tokens=total_tokens if total_tokens > 0 else None,
            model_breakdown=model_breakdown if model_breakdown else None,
            metadata={"date": start_date}
        )
        
    @staticmethod
    def from_env() -> Optional['OpenAIAdapter']:
        """Create adapter from environment variables"""
        api_keys = []
        
        # Check for single key
        key = os.getenv("OPENAI_API_KEY")
        if key:
            api_keys.append(key)
            
        # Check for multiple keys (OPENAI_API_KEY_1, OPENAI_API_KEY_2, etc.)
        i = 1
        while True:
            key = os.getenv(f"OPENAI_API_KEY_{i}")
            if not key:
                break
            api_keys.append(key)
            i += 1
            
        if not api_keys:
            return None
            
        config = ProviderConfig(
            name="openai",
            display_name="OpenAI",
            api_keys=api_keys
        )
        
        return OpenAIAdapter(config)