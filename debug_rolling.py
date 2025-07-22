#!/usr/bin/env python3
"""Debug rolling session detection"""
import sys
import os
from datetime import datetime, timezone, timedelta
import json
import glob
from pathlib import Path

# Find message times
claude_dir = Path.home() / ".claude" / "projects"
now = datetime.now(timezone.utc).replace(tzinfo=None)
five_hours_ago = now - timedelta(hours=5)
ten_hours_ago = now - timedelta(hours=10)

pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = sorted(glob.glob(pattern, recursive=True), key=os.path.getmtime, reverse=True)

print(f"Current time: {now}")
print(f"Looking for messages since: {ten_hours_ago}")
print(f"\nChecking {len(jsonl_files)} files...")

# Collect all message timestamps
message_times = []

for file_path in jsonl_files[:5]:  # Check recent files
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    if mtime < ten_hours_ago:
        continue
        
    print(f"\nFile: {os.path.basename(file_path)}")
    print(f"Modified: {mtime}")
    
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                
                if entry.get('type') == 'assistant' and entry.get('message', {}).get('usage'):
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')).replace(tzinfo=None)
                    message_times.append(timestamp)
                    count += 1
                    
                    if count <= 3:  # Show first few
                        print(f"  Message at: {timestamp}")
                        
            except:
                continue
                
    print(f"  Found {count} messages with usage data")

# Sort and analyze gaps
message_times.sort()
print(f"\nTotal messages found: {len(message_times)}")

if message_times:
    print("\nRecent messages and gaps:")
    # Show last 50 messages to find session boundaries
    for i in range(max(0, len(message_times) - 50), len(message_times)):
        msg_time = message_times[i]
        hours_ago = (now - msg_time).total_seconds() / 3600
        
        gap_str = ""
        if i > 0:
            gap = (msg_time - message_times[i-1]).total_seconds() / 3600
            if gap > 5:
                gap_str = f" [NEW SESSION - {gap:.1f}h gap]"
            else:
                gap_str = f" [{gap:.1f}h gap]"
                
        print(f"  {msg_time} ({hours_ago:.1f}h ago){gap_str}")