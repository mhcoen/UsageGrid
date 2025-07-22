#!/usr/bin/env python3
"""
Test script for demo version with mock data
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting LLM Cost Monitor Demo...")
print("This shows a working UI with simulated data.")
print("The OpenAI card will show changing mock data.")
print()

# Run the demo version
from src.main_simple_async import main

if __name__ == "__main__":
    main()