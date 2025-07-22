#!/usr/bin/env python3
"""
Test script for async version
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the async version
from src.main_async_clean import main

if __name__ == "__main__":
    print("Starting LLM Cost Monitor (Async Version)...")
    print("This version includes real-time polling.")
    print()
    
    # Check for API keys
    providers = ["OPENAI", "ANTHROPIC", "OPENROUTER", "HUGGINGFACE"]
    found_keys = []
    
    for provider in providers:
        if os.getenv(f"{provider}_API_KEY"):
            found_keys.append(provider)
            
    if found_keys:
        print(f"Found API keys for: {', '.join(found_keys)}")
    else:
        print("No API keys found. The app will run but won't fetch real data.")
        print("Set environment variables like OPENAI_API_KEY to enable providers.")
    
    print()
    main()