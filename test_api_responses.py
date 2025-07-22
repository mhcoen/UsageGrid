#!/usr/bin/env python3
"""
Quick test to see API responses without UI
"""
import os
import sys
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.openai_adapter import OpenAIAdapter
from src.providers.anthropic_adapter import AnthropicAdapter
from src.providers.openrouter_adapter import OpenRouterAdapter
from src.providers.huggingface_adapter import HuggingFaceAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_providers():
    """Test each provider and show the data"""
    
    # OpenAI
    openai = OpenAIAdapter.from_env()
    if openai:
        print("\n=== OpenAI ===")
        try:
            await openai.initialize()
            data = await openai.fetch_usage()
            print(f"Cost: ${data.total_cost}")
            print(f"Tokens: {data.total_tokens}")
            print(f"Models: {data.model_breakdown}")
            print(f"Metadata: {data.metadata}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await openai.cleanup()
    
    # Anthropic
    anthropic = AnthropicAdapter.from_env()
    if anthropic:
        print("\n=== Anthropic ===")
        try:
            await anthropic.initialize()
            data = await anthropic.fetch_usage()
            print(f"Cost: ${data.total_cost}")
            print(f"Tokens: {data.total_tokens}")
            print(f"Models: {data.model_breakdown}")
            print(f"Metadata: {data.metadata}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await anthropic.cleanup()
    
    # OpenRouter
    openrouter = OpenRouterAdapter.from_env()
    if openrouter:
        print("\n=== OpenRouter ===")
        try:
            await openrouter.initialize()
            data = await openrouter.fetch_usage()
            print(f"Cost: ${data.total_cost}")
            print(f"Tokens: {data.total_tokens}")
            print(f"Models: {data.model_breakdown}")
            print(f"Metadata: {data.metadata}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await openrouter.cleanup()
    
    # HuggingFace
    huggingface = HuggingFaceAdapter.from_env()
    if huggingface:
        print("\n=== HuggingFace ===")
        try:
            await huggingface.initialize()
            data = await huggingface.fetch_usage()
            print(f"Cost: ${data.total_cost}")
            print(f"Tokens: {data.total_tokens}")
            print(f"Models: {data.model_breakdown}")
            print(f"Metadata: {data.metadata}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await huggingface.cleanup()


if __name__ == "__main__":
    asyncio.run(test_providers())