#!/usr/bin/env python3
"""
Test script with real API keys to see actual data
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting LLM Cost Monitor with REAL API KEYS...")
print("This will attempt to fetch real usage data.")
print()

# Check for API keys
providers = {
    "OPENAI_API_KEY": "OpenAI",
    "ANTHROPIC_API_KEY": "Anthropic", 
    "OPENROUTER_API_KEY": "OpenRouter",
    "HUGGINGFACE_API_TOKEN": "HuggingFace",
    "HF_TOKEN": "HuggingFace"
}

found_keys = []
for env_var, provider in providers.items():
    if os.getenv(env_var) and provider not in found_keys:
        found_keys.append(provider)

if found_keys:
    print(f"Found API keys for: {', '.join(found_keys)}")
else:
    print("No API keys found!")
    sys.exit(1)

print("\nStarting application...")
print("-" * 50)

# Run the async version
from src.main_async_clean import main

if __name__ == "__main__":
    main()