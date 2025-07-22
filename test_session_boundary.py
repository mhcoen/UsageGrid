#!/usr/bin/env python3
"""Debug session boundary issue"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

# Test with very small increments around 1 hour mark
now = datetime.utcnow()
reader = ClaudeCodeReader()

print("Testing time boundaries...")
print(f"Current time: {now}")
print("-" * 50)

# Test in 10-minute increments
for minutes in range(30, 90, 10):
    since = now - timedelta(minutes=minutes)
    data = reader.get_usage_data(since_date=since)
    
    if data['total_cost'] > 0:
        print(f"\nLast {minutes} minutes:")
        print(f"  Cost: ${data['total_cost']:.2f}")
        print(f"  Tokens: {data['total_tokens']:,}")
        print(f"  Messages: {data.get('session_count', 0)}")

# Also test the exact current session window
print("\n" + "="*50)
print("Testing 5-hour session window...")

# Round down to hour like Claude Monitor does
session_start = now.replace(minute=0, second=0, microsecond=0)
# Find the session start (could be up to 5 hours ago)
for hours_back in range(6):
    test_start = session_start - timedelta(hours=hours_back)
    test_data = reader.get_usage_data(since_date=test_start)
    
    if test_data['total_cost'] > 0:
        print(f"\nSession starting {hours_back} hours ago at {test_start}:")
        print(f"  Cost: ${test_data['total_cost']:.2f}")
        print(f"  Tokens: {test_data['total_tokens']:,}")
        print(f"  Messages: {test_data.get('session_count', 0)}")
        break