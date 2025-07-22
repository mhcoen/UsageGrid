#!/usr/bin/env python3
"""Test to find the correct session values"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

reader = ClaudeCodeReader()

# Test different time windows to find the one that matches $23.67
print("Finding the correct session window...")
print("Target: $23.67 with ~26,247 tokens")
print("-" * 50)

now = datetime.utcnow()

# Test from 30 minutes to 3 hours in 10-minute increments
for minutes in range(30, 180, 10):
    since = now - timedelta(minutes=minutes)
    data = reader.get_usage_data(since_date=since)
    
    cost = data['total_cost']
    tokens = data['total_tokens']
    
    # Check if we're close to the target
    if 20 < cost < 30 and 20000 < tokens < 35000:
        print(f"\n✓ Last {minutes} minutes ({minutes/60:.1f} hours):")
        print(f"  Cost: ${cost:.2f}")
        print(f"  Tokens: {tokens:,}")
        print(f"  Messages: {data.get('session_count', 0)}")
        
        # Check if this is close to our target
        if abs(cost - 23.67) < 2:
            print(f"  >>> This looks like the correct window! <<<")

# Also check exact hour boundaries
print("\n" + "="*50)
print("Checking hour boundaries:")

for hours in [1, 1.5, 2, 2.5, 3]:
    since = now - timedelta(hours=hours)
    data = reader.get_usage_data(since_date=since)
    
    cost = data['total_cost']
    tokens = data['total_tokens']
    
    print(f"\nLast {hours} hours:")
    print(f"  Cost: ${cost:.2f}")
    print(f"  Tokens: {tokens:,}")
    
    if abs(cost - 23.67) < 1:
        print(f"  >>> MATCH! This is very close to $23.67 <<<")
    if abs(tokens - 26247) < 5000:
        print(f"  >>> Token count is close to 26,247 <<<")