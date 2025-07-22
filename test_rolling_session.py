#!/usr/bin/env python3
"""Test rolling session detection"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader
from src.utils.session_helper import find_session_start

reader = ClaudeCodeReader()
now = datetime.now(timezone.utc).replace(tzinfo=None)

# Find current session start
print("Finding session start...")
session_start = find_session_start(now)
hours_in = (now - session_start).total_seconds() / 3600

print(f"\nCurrent time: {now}")
print(f"Session started: {session_start}")
print(f"Hours into session: {hours_in:.1f}")

# Get data for current session
data = reader.get_usage_data(since_date=session_start)
tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())

print(f"\nSession tokens: {tokens:,}")
print("Claude Monitor shows: 39,816 tokens")