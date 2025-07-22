#!/usr/bin/env python3
"""Find the actual current session start time"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import json
import glob
from pathlib import Path

# Get current time
now = datetime.utcnow()
print(f"Current time: {now}")
print("-" * 50)

# Look for message timestamps to find session boundaries
claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = glob.glob(pattern, recursive=True)

# Collect all timestamps with usage in last 8 hours
timestamps = []
eight_hours_ago = now - timedelta(hours=8)

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
                            if ts_naive >= eight_hours_ago:
                                timestamps.append(ts_naive)
                except:
                    pass

# Sort timestamps
timestamps.sort()

if timestamps:
    print(f"Found {len(timestamps)} messages in last 8 hours")
    print(f"First message: {timestamps[0]} ({(now - timestamps[0]).total_seconds() / 3600:.1f} hours ago)")
    print(f"Last message: {timestamps[-1]} ({(now - timestamps[-1]).total_seconds() / 60:.1f} minutes ago)")
    
    # Find gaps of > 1 hour to identify session boundaries
    print("\nLooking for session boundaries (gaps > 1 hour):")
    last_ts = timestamps[0]
    sessions = [[timestamps[0]]]
    
    for ts in timestamps[1:]:
        gap = (ts - last_ts).total_seconds() / 3600
        if gap > 1.0:  # More than 1 hour gap
            print(f"  Gap of {gap:.1f} hours between {last_ts} and {ts}")
            sessions.append([ts])
        else:
            sessions[-1].append(ts)
        last_ts = ts
    
    print(f"\nFound {len(sessions)} sessions")
    current_session = sessions[-1]
    print(f"Current session:")
    print(f"  Started: {current_session[0]} ({(now - current_session[0]).total_seconds() / 3600:.1f} hours ago)")
    print(f"  Messages: {len(current_session)}")
    print(f"  Duration: {(current_session[-1] - current_session[0]).total_seconds() / 60:.1f} minutes")