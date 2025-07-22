#!/usr/bin/env python3
"""Simple session debugging"""
import sys
import os
from datetime import datetime, timezone, timedelta
import json
import glob
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader

# Current time
now = datetime.now(timezone.utc).replace(tzinfo=None)
central_offset = timedelta(hours=5)  # UTC-5 for Central Daylight Time (CDT)
now_central = now - central_offset

print(f"Current UTC time: {now}")
print(f"Current Central time: {now_central.strftime('%I:%M %p')}")
print()

# Check different potential session starts
reader = ClaudeCodeReader()

print("Checking potential session starts (in Central time):")
for hour in range(10):  # Check last 10 hours
    # Calculate potential session start in UTC
    potential_start_central = now_central.replace(hour=now_central.hour - hour, minute=0, second=0, microsecond=0)
    if potential_start_central > now_central:
        potential_start_central -= timedelta(days=1)
    
    potential_start_utc = potential_start_central + central_offset
    
    # Skip if this would be more than 5 hours ago
    if (now - potential_start_utc).total_seconds() / 3600 > 5:
        continue
    
    # Get tokens for this window
    data = reader.get_usage_data(since_date=potential_start_utc)
    tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())
    
    hours_ago = (now - potential_start_utc).total_seconds() / 3600
    print(f"  {potential_start_central.strftime('%I:%M %p')} ({hours_ago:.1f}h ago): {tokens:,} tokens")

print("\nClaude Monitor shows: 39,816 tokens")