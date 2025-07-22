#!/usr/bin/env python3
"""Test that we get the right session"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.session_helper import find_session_start
from src.providers.claude_code_reader import ClaudeCodeReader

now = datetime.now(timezone.utc).replace(tzinfo=None)

# Find session using our logic
session_start = find_session_start(now)
print(f"Session finder returned: {session_start} UTC")
print(f"Session finder returned: {(session_start - timedelta(hours=5)).strftime('%I:%M %p')} Central")

# Get tokens
reader = ClaudeCodeReader()
data = reader.get_usage_data(since_date=session_start)
tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())

print(f"\nTokens: {tokens:,}")
print("Claude Monitor: 39,816")

# Let's also manually check midnight UTC (7PM Central)
midnight_utc = datetime(2025, 7, 21, 0, 0, 0)
data2 = reader.get_usage_data(since_date=midnight_utc)
tokens2 = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data2['model_breakdown'].values())
print(f"\nManual check - Midnight UTC (7PM Central): {tokens2:,} tokens")