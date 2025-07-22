#!/usr/bin/env python3
"""
Test the simple version with real data
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting Simple LLM Cost Monitor with Real API Data...")
print("This version avoids complex async issues.")
print()

# Check for API keys
providers = {
    "OPENAI_API_KEY": "OpenAI",
    "ANTHROPIC_API_KEY": "Anthropic", 
    "OPENROUTER_API_KEY": "OpenRouter",
    "GEMINI_API_KEY": "Gemini",
    "GOOGLE_API_KEY": "Gemini"
}

found_keys = []
for env_var, provider in providers.items():
    if os.getenv(env_var) and provider not in found_keys:
        found_keys.append(provider)

if found_keys:
    print(f"Found API keys for: {', '.join(found_keys)}")

print("\nData will update every 5 seconds.")
print("-" * 50)

# Run the simple version
from src.main_real_simple import main

if __name__ == "__main__":
    main()