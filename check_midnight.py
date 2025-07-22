#!/usr/bin/env python3
"""Check if session started around midnight"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader

reader = ClaudeCodeReader()
now = datetime.now(timezone.utc).replace(tzinfo=None)

print(f"Current time: {now}")
print("\nChecking different time windows:")

# Check different starting points
for hours_back in [1.5, 2.0, 2.1, 2.2, 2.3, 2.5, 3.0]:
    since = now - timedelta(hours=hours_back)
    data = reader.get_usage_data(since_date=since)
    tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())
    print(f"{hours_back:3.1f} hours ago ({since.strftime('%H:%M')}): {tokens:,} tokens")

print("\nClaude Monitor shows: 39,816 tokens")