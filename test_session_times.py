#!/usr/bin/env python3
"""Debug Claude Code session timestamps"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta, timezone
import json
import glob
from pathlib import Path

# Get current time info
now_utc = datetime.now(timezone.utc)
now_naive = datetime.utcnow()

print(f"Current UTC time (aware): {now_utc}")
print(f"Current UTC time (naive): {now_naive}")
print(f"Time difference: {now_utc.replace(tzinfo=None) - now_naive}")
print("-" * 50)

# Look at a few recent entries
claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = sorted(glob.glob(pattern, recursive=True), key=os.path.getmtime, reverse=True)

print(f"\nChecking most recent JSONL file: {jsonl_files[0]}")
print("Last 5 entries with timestamps:")

entries_with_usage = []
with open(jsonl_files[0], 'r') as f:
    for line in f:
        if line.strip():
            try:
                entry = json.loads(line)
                if entry.get('message', {}).get('usage'):
                    timestamp_str = entry.get('timestamp')
                    if timestamp_str:
                        entries_with_usage.append({
                            'timestamp': timestamp_str,
                            'usage': entry['message']['usage'],
                            'model': entry.get('message', {}).get('model', 'unknown')
                        })
            except:
                pass

# Show last 5 entries
for entry in entries_with_usage[-5:]:
    ts = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
    ts_naive = ts.replace(tzinfo=None)
    hours_ago = (now_naive - ts_naive).total_seconds() / 3600
    
    print(f"\n  Time: {entry['timestamp']}")
    print(f"  Hours ago: {hours_ago:.1f}")
    print(f"  Model: {entry['model']}")
    print(f"  Tokens: {entry['usage'].get('input_tokens', 0) + entry['usage'].get('output_tokens', 0)}")