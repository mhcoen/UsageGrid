#!/usr/bin/env python3
"""Test current session to match Claude Code's actual numbers"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta
import json
import glob
from pathlib import Path

# Check the most recent activity
now = datetime.utcnow()
reader = ClaudeCodeReader()

print("Checking Claude Code session data...")
print(f"Current time: {now}")
print("-" * 50)

# Test different windows to find where the data is
for hours in [0.5, 1, 2, 3, 4, 5, 6]:
    since = now - timedelta(hours=hours)
    data = reader.get_usage_data(since_date=since)
    
    print(f"\nLast {hours} hours:")
    print(f"  Cost: ${data['total_cost']:.2f}")
    print(f"  Tokens: {data['total_tokens']:,}")
    print(f"  Messages: {data.get('session_count', 0)}")

# Also check the raw message count
claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = glob.glob(pattern, recursive=True)

# Count messages with usage in current session
session_start = now - timedelta(hours=5)
message_count = 0
total_cost = 0.0

for file_path in jsonl_files:
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get('message', {}).get('usage'):
                        timestamp_str = entry.get('timestamp')
                        if timestamp_str:
                            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            ts_naive = ts.replace(tzinfo=None)
                            
                            # Check if in current session window
                            if ts_naive >= session_start:
                                message_count += 1
                except:
                    pass

print(f"\nRaw message count in 5-hour window: {message_count}")

# Get the actual session ID or project file
recent_file = max(jsonl_files, key=os.path.getmtime)
print(f"\nMost recent file: {os.path.basename(recent_file)}")
print(f"Project: {os.path.basename(os.path.dirname(recent_file))}")