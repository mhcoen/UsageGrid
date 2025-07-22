#!/usr/bin/env python3
"""Test the session logic with rounding"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.session_helper import find_session_start, round_to_hour
from src.providers.claude_code_reader import ClaudeCodeReader

# Current time (in Central time as you mentioned)
now = datetime.now(timezone.utc).replace(tzinfo=None)
print(f"Current UTC time: {now}")
print(f"Current Central time: {(now - timedelta(hours=6)).strftime('%I:%M %p')}")  # UTC-6 for Central

# Find session start
session_start = find_session_start(now)
print(f"\nSession started at: {session_start}")
print(f"Session started (Central): {(session_start - timedelta(hours=6)).strftime('%I:%M %p')}")
print(f"Hours into session: {(now - session_start).total_seconds() / 3600:.1f}")

# Get token count for this session
reader = ClaudeCodeReader()
data = reader.get_usage_data(since_date=session_start)
tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())

print(f"\nSession tokens: {tokens:,}")
print("Claude Monitor shows: 39,816 tokens")

# Let's also check what happens if we look at the previous hour boundary
from datetime import timedelta
prev_hour = round_to_hour(now - timedelta(hours=1))
print(f"\nPrevious hour boundary: {prev_hour}")
data2 = reader.get_usage_data(since_date=prev_hour)
tokens2 = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data2['model_breakdown'].values())
print(f"Tokens from {prev_hour}: {tokens2:,}")