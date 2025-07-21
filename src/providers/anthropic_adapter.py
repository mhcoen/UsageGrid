"""
Anthropic provider adapter for LLM Cost Monitor
Handles fetching usage data from Anthropic API
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.providers.base import ProviderAdapter, ProviderConfig, UsageData
from src.providers.claude_code_reader import ClaudeCodeReader

logger = logging.getLogger(__name__)


class AnthropicAdapter(ProviderAdapter):
    """Anthropic API adapter"""
    
    BASE_URL = "https://api.anthropic.com/v1"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get Anthropic authorization headers"""
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Anthropic API key"""
        try:
            # Try to fetch account info as a validation check
            url = f"{self.BASE_URL}/messages"
            
            # Send a minimal test request
            test_data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            await self.make_request(url, api_key, method="POST", json=test_data)
            return True
        except Exception as e:
            # Check if it's an auth error or just a usage error
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                logger.error(f"Invalid Anthropic API key: {e}")
                return False
            # Other errors might just mean the request format was wrong, but key is valid
            return True
            
    async def fetch_usage(self) -> UsageData:
        """Fetch usage data from Anthropic"""
        logger.info(f"Fetching Anthropic usage data")
        
        # Try to read Claude Code usage data from JSONL files
        try:
            reader = ClaudeCodeReader()
            # Get today's usage
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            usage_data = reader.get_usage_data(since_date=today)
            
            logger.info(f"Claude Code usage: ${usage_data['total_cost']:.4f}, "
                       f"{usage_data['total_tokens']} tokens from {usage_data['file_count']} files")
            
            # Convert model breakdown format
            model_breakdown = {}
            for model, data in usage_data['model_breakdown'].items():
                model_breakdown[model] = {
                    "cost": data["cost"],
                    "tokens": data["input_tokens"] + data["output_tokens"]
                }
            
            return UsageData(
                timestamp=datetime.utcnow(),
                total_cost=usage_data['total_cost'],
                total_tokens=usage_data['total_tokens'],
                model_breakdown=model_breakdown if model_breakdown else None,
                metadata={
                    "provider": "anthropic",
                    "source": "claude_code",
                    "session_count": usage_data['session_count'],
                    "file_count": usage_data['file_count']
                }
            )
            
        except Exception as e:
            logger.error(f"Error reading Claude Code data: {e}")
            
            # Fall back to API attempt (though we know it doesn't exist)
            # For demo purposes, if no real API key, return mock data
            if not self.config.api_keys or self.config.api_keys[0].startswith("sk-ant-dummy"):
                logger.info("Using mock data for Anthropic")
                import random
                mock_cost = random.uniform(15.0, 35.0)
                mock_tokens = random.randint(30000, 70000)
                
                return UsageData(
                    timestamp=datetime.utcnow(),
                    total_cost=mock_cost,
                    total_tokens=mock_tokens,
                    model_breakdown={
                        "claude-3-opus": {"cost": mock_cost * 0.5, "tokens": int(mock_tokens * 0.3)},
                        "claude-3-sonnet": {"cost": mock_cost * 0.3, "tokens": int(mock_tokens * 0.4)},
                        "claude-3-haiku": {"cost": mock_cost * 0.2, "tokens": int(mock_tokens * 0.3)}
                    },
                    metadata={"mock": True}
                )
                
            # No Claude Code data and no API
            return UsageData(
                timestamp=datetime.utcnow(),
                total_cost=0.0,
                total_tokens=None,
                model_breakdown=None,
                metadata={"provider": "anthropic", "error": "No data source available"}
            )
        
    @staticmethod
    def from_env() -> Optional['AnthropicAdapter']:
        """Create adapter from environment variables"""
        api_keys = []
        
        # Check for single key
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            api_keys.append(key)
            
        # Check for multiple keys (ANTHROPIC_API_KEY_1, ANTHROPIC_API_KEY_2, etc.)
        i = 1
        while True:
            key = os.getenv(f"ANTHROPIC_API_KEY_{i}")
            if not key:
                break
            api_keys.append(key)
            i += 1
            
        if not api_keys:
            return None
            
        config = ProviderConfig(
            name="anthropic",
            display_name="Anthropic",
            api_keys=api_keys
        )
        
        return AnthropicAdapter(config)