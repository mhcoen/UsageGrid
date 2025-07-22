#!/usr/bin/env python3
"""Find the actual session start"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.session_helper import find_session_start
from src.providers.claude_code_reader import ClaudeCodeReader

now = datetime.now(timezone.utc).replace(tzinfo=None)
print(f"Current time: {now}")

# Use our session finder
session_start = find_session_start(now)
print(f"\nSession finder returned: {session_start}")

# Let's manually check - the session started about 2 hours ago based on your observation
two_hours_ago = now - timedelta(hours=2)
print(f"\nChecking 2 hours ago: {two_hours_ago}")

reader = ClaudeCodeReader()
data = reader.get_usage_data(since_date=two_hours_ago)
tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())
print(f"Tokens from 2 hours ago: {tokens:,}")

# The issue is our session finder is looking at ALL messages in the last 5 hours
# But if there's continuous activity, it won't find gaps
# We need to look BEYOND 5 hours to find when the previous session ended

print("\nLet me find the actual session start by looking for gaps...")

# Import what we need
import json
import glob
from pathlib import Path

claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = sorted(glob.glob(pattern, recursive=True), key=os.path.getmtime, reverse=True)

# Look back up to 10 hours
ten_hours_ago = now - timedelta(hours=10)
message_times = []

for file_path in jsonl_files:
    if os.path.getmtime(file_path) < ten_hours_ago.timestamp():
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('type') == 'assistant' and entry.get('message', {}).get('usage'):
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')).replace(tzinfo=None)
                    if timestamp <= now:  # Only past messages
                        message_times.append(timestamp)
            except:
                continue

message_times.sort(reverse=True)  # Most recent first

print(f"\nFound {len(message_times)} messages")
print("\nLooking for session start (gap > 5 hours)...")

session_start_found = None
for i in range(len(message_times) - 1):
    current = message_times[i]
    previous = message_times[i + 1]
    gap_hours = (current - previous).total_seconds() / 3600
    
    if gap_hours > 5:
        session_start_found = current
        print(f"\nFound session start!")
        print(f"  Previous message: {previous}")
        print(f"  Gap: {gap_hours:.1f} hours")
        print(f"  Session started: {current}")
        print(f"  Hours ago: {(now - current).total_seconds() / 3600:.1f}")
        break
        
    # Show recent activity
    if i < 5:
        hours_ago = (now - current).total_seconds() / 3600
        print(f"  {current} ({hours_ago:.1f}h ago, gap: {gap_hours:.1f}h)")

if session_start_found:
    # Check tokens for this session
    data = reader.get_usage_data(since_date=session_start_found)
    tokens = sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in data['model_breakdown'].values())
    print(f"\nTokens from session start: {tokens:,}")