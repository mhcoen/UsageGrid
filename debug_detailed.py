#!/usr/bin/env python3
"""Debug token counting in detail"""
import sys
import os
from datetime import datetime, timedelta, timezone
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader

reader = ClaudeCodeReader()
now = datetime.now(timezone.utc).replace(tzinfo=None)

# Get current session data (5 hours)
five_hours_ago = now - timedelta(hours=5)

# Let's manually read and check a few recent entries
import glob
from pathlib import Path

claude_dir = Path.home() / ".claude" / "projects"
pattern = str(claude_dir / "**" / "*.jsonl")
jsonl_files = sorted(glob.glob(pattern, recursive=True), key=os.path.getmtime, reverse=True)

print(f"Checking most recent JSONL file: {jsonl_files[0]}")
print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(jsonl_files[0]))}")
print()

# Read last few entries
entries_checked = 0
total_input = 0
total_output = 0

with open(jsonl_files[0], 'r') as f:
    lines = f.readlines()
    print(f"File has {len(lines)} entries")
    
    # Find usage entries
    usage_entries = []
    for line in lines:
        try:
            entry = json.loads(line.strip())
            if entry.get('type') == 'usage':
                usage_entries.append(entry)
        except:
            pass
    
    print(f"Found {len(usage_entries)} usage entries")
    print("\nLast 5 usage entries:")
    
    for entry in usage_entries[-5:]:
        try:
            print(f"\n  Entry type: {entry.get('type')}")
            if entry.get('type') == 'usage':
                timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')).replace(tzinfo=None)
                request_data = entry.get('requestData', {})
                response_data = entry.get('responseData', {})
                
                # Get token counts
                input_tokens = request_data.get('usage', {}).get('input_tokens', 0)
                cache_creation = request_data.get('usage', {}).get('cache_creation_input_tokens', 0)
                cache_read = request_data.get('usage', {}).get('cache_read_input_tokens', 0)
                output_tokens = response_data.get('usage', {}).get('output_tokens', 0)
                
                print(f"\n  Time: {timestamp}")
                print(f"  Input: {input_tokens}, Cache create: {cache_creation}, Cache read: {cache_read}")
                print(f"  Output: {output_tokens}")
                print(f"  Non-cache total: {input_tokens + output_tokens}")
                
                if timestamp >= five_hours_ago:
                    total_input += input_tokens
                    total_output += output_tokens
                    entries_checked += 1
                    
        except Exception as e:
            print(f"Error reading entry: {e}")

print(f"\n\nManual count for entries in last 5 hours:")
print(f"  Entries checked: {entries_checked}")
print(f"  Total input: {total_input:,}")
print(f"  Total output: {total_output:,}")
print(f"  Total non-cache: {total_input + total_output:,}")

# Now compare with our reader
session_data = reader.get_usage_data(since_date=five_hours_ago)
print(f"\nReader results:")
print(f"  Total input (from model_breakdown): {sum(m.get('input_tokens', 0) for m in session_data['model_breakdown'].values()):,}")
print(f"  Total output (from model_breakdown): {sum(m.get('output_tokens', 0) for m in session_data['model_breakdown'].values()):,}")
print(f"  Total non-cache: {sum(m.get('input_tokens', 0) + m.get('output_tokens', 0) for m in session_data['model_breakdown'].values()):,}")