#!/usr/bin/env python3
"""Debug timezone issue in Claude Code reader"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import json
import glob
from pathlib import Path

# Test timezone conversion
test_timestamp = "2025-07-21T00:37:19.494Z"
print(f"Test timestamp: {test_timestamp}")

# Method 1 - what we're doing
ts1 = datetime.fromisoformat(test_timestamp.replace('Z', '+00:00'))
ts1_naive = ts1.replace(tzinfo=None)
print(f"Method 1 (replace tzinfo): {ts1_naive}")

# Method 2 - what we should do
ts2 = datetime.fromisoformat(test_timestamp.replace('Z', '+00:00'))
ts2_utc = ts2.astimezone().replace(tzinfo=None)  # Convert to local then strip
print(f"Method 2 (astimezone): {ts2_utc}")

# Check current time
now = datetime.utcnow()
print(f"\nCurrent UTC time: {now}")
print(f"Hours difference (method 1): {(now - ts1_naive).total_seconds() / 3600:.2f}")
print(f"Hours difference (method 2): {(now - ts2_utc).total_seconds() / 3600:.2f}")

# Check what happens with a 5-hour window
five_hours_ago = now - timedelta(hours=5)
print(f"\n5 hours ago: {five_hours_ago}")
print(f"Test timestamp is after 5 hours ago: {ts1_naive > five_hours_ago}")

# Look for entries in different time windows
claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = glob.glob(pattern, recursive=True)

counts = {1: 0, 5: 0, 24: 0}
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
                            hours_ago = (now - ts_naive).total_seconds() / 3600
                            
                            if hours_ago <= 1:
                                counts[1] += 1
                            if hours_ago <= 5:
                                counts[5] += 1
                            if hours_ago <= 24:
                                counts[24] += 1
                except:
                    pass

print(f"\nMessage counts by time window:")
print(f"Last 1 hour: {counts[1]}")
print(f"Last 5 hours: {counts[5]}")
print(f"Last 24 hours: {counts[24]}")