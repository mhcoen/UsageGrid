"""
HuggingFace provider adapter for LLM Cost Monitor
Handles fetching usage data from HuggingFace API
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from src.providers.base import ProviderAdapter, ProviderConfig, UsageData

logger = logging.getLogger(__name__)


class HuggingFaceAdapter(ProviderAdapter):
    """HuggingFace API adapter"""
    
    BASE_URL = "https://api-inference.huggingface.co"
    HUB_URL = "https://huggingface.co"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get HuggingFace authorization headers"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate HuggingFace API key"""
        try:
            # Try to get user info
            url = f"{self.HUB_URL}/api/whoami"
            response = await self.make_request(url, api_key)
            
            # If we get a response with a username, the key is valid
            return "name" in response or "id" in response
            
        except Exception as e:
            logger.error(f"Invalid HuggingFace API key: {e}")
            return False
            
    async def fetch_usage(self) -> UsageData:
        """Fetch usage data from HuggingFace"""
        logger.info(f"Fetching HuggingFace usage data with {len(self.config.api_keys)} API keys")
        
        # For demo purposes, if no real API key, return mock data
        if not self.config.api_keys or self.config.api_keys[0].startswith("hf_dummy"):
            logger.info("Using mock data for HuggingFace")
            import random
            mock_cost = random.uniform(8.0, 30.0)
            mock_compute_hours = random.uniform(10.0, 50.0)
            
            return UsageData(
                timestamp=datetime.utcnow(),
                total_cost=mock_cost,
                total_tokens=None,  # HF tracks compute hours, not tokens
                model_breakdown={
                    "Inference API": {"cost": mock_cost * 0.3, "compute_hours": mock_compute_hours * 0.3},
                    "Spaces GPU": {"cost": mock_cost * 0.5, "compute_hours": mock_compute_hours * 0.5},
                    "AutoTrain": {"cost": mock_cost * 0.2, "compute_hours": mock_compute_hours * 0.2}
                },
                metadata={"mock": True, "compute_hours": mock_compute_hours}
            )
        
        # Initialize totals
        total_cost = 0.0
        total_compute_hours = 0.0
        service_breakdown = {}
        
        for api_key in self.config.api_keys:
            try:
                # HuggingFace billing endpoint (this would need to be verified)
                # The actual endpoint might be different
                url = f"{self.HUB_URL}/api/billing/usage"
                
                logger.info(f"Requesting HuggingFace usage from: {url}")
                
                response = await self.make_request(url, api_key)
                
                logger.info(f"HuggingFace response: {response}")
                
                # Parse response (structure would need to be verified)
                if "usage" in response:
                    for service, data in response["usage"].items():
                        cost = data.get("cost", 0.0)
                        hours = data.get("compute_hours", 0.0)
                        
                        total_cost += cost
                        total_compute_hours += hours
                        
                        if service not in service_breakdown:
                            service_breakdown[service] = {"cost": 0.0, "compute_hours": 0.0}
                        
                        service_breakdown[service]["cost"] += cost
                        service_breakdown[service]["compute_hours"] += hours
                        
                elif "total_spent" in response:
                    # Alternative response format
                    total_cost += response.get("total_spent", 0.0)
                    
            except Exception as e:
                logger.error(f"Error fetching HuggingFace usage: {e}")
                # Continue with other API keys
                
        return UsageData(
            timestamp=datetime.utcnow(),
            total_cost=total_cost,
            total_tokens=None,  # HuggingFace doesn't use token-based billing
            model_breakdown=service_breakdown if service_breakdown else None,
            metadata={
                "provider": "huggingface",
                "compute_hours": total_compute_hours
            }
        )
        
    @staticmethod
    def from_env() -> Optional['HuggingFaceAdapter']:
        """Create adapter from environment variables"""
        api_keys = []
        
        # Check for single key (common env var names)
        for env_var in ["HUGGINGFACE_API_TOKEN", "HUGGINGFACE_API_KEY", "HF_TOKEN"]:
            key = os.getenv(env_var)
            if key:
                api_keys.append(key)
                break
                
        # Check for multiple keys
        i = 1
        while True:
            key = os.getenv(f"HUGGINGFACE_API_TOKEN_{i}")
            if not key:
                break
            api_keys.append(key)
            i += 1
            
        if not api_keys:
            return None
            
        config = ProviderConfig(
            name="huggingface",
            display_name="HuggingFace",
            api_keys=api_keys
        )
        
        return HuggingFaceAdapter(config)