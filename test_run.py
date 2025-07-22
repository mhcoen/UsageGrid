#!/usr/bin/env python3
"""
Test script to verify basic functionality
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a dummy API key for testing if none exists
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: No OPENAI_API_KEY found in environment")
    print("The app will start but won't be able to fetch real data")
    # os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"

# Run the main application
from src.main import main

if __name__ == "__main__":
    main()