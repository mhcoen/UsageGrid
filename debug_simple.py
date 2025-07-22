#!/usr/bin/env python3
"""Simple check of Claude Monitor vs our calculation"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader

reader = ClaudeCodeReader()
now = datetime.now(timezone.utc).replace(tzinfo=None)

# Get 5-hour session
five_hours_ago = now - timedelta(hours=5)
data = reader.get_usage_data(since_date=five_hours_ago)

print("Claude Monitor shows: 39,816 tokens")
print(f"We calculate: {sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values()):,} tokens")
print()

# Maybe the issue is we're looking at the wrong session window?
# Try different windows
for hours in [1, 2, 3, 4, 5, 6]:
    since = now - timedelta(hours=hours)
    data = reader.get_usage_data(since_date=since)
    tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())
    print(f"{hours} hours: {tokens:,} tokens")