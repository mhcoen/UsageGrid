#!/usr/bin/env python3
"""
Test script with mock data for demonstration
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a dummy API key to enable the provider
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-demo"

print("Starting LLM Cost Monitor with MOCK DATA...")
print("This will show simulated data for demonstration purposes.")
print()

# Run the async version
from src.main_async_clean import main

if __name__ == "__main__":
    main()