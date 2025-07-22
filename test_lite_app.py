#!/usr/bin/env python3
"""Test the lite app and show any errors"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting LLM Cost Monitor Lite...")
print("If the app crashes, errors will be shown below.")
print("-" * 50)

try:
    from src.main_simple_lite import main
    main()
except Exception as e:
    print(f"\nApp crashed with error: {e}")
    import traceback
    traceback.print_exc()