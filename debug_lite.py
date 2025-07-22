#!/usr/bin/env python3
"""Debug the lite app crash"""
import sys
import os
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting app...")
    from src.main_simple_lite import main
    main()
except Exception as e:
    print(f"\n=== APP CRASHED ===")
    print(f"Error: {e}")
    print(f"Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    print("==================")