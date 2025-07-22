#!/usr/bin/env python3
"""Debug token counting"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.providers.claude_code_reader import ClaudeCodeReader

reader = ClaudeCodeReader()
now = datetime.now(timezone.utc).replace(tzinfo=None)

# Get current session data (5 hours)
five_hours_ago = now - timedelta(hours=5)
session_data = reader.get_usage_data(since_date=five_hours_ago)

print(f"Session data (5 hours):")
print(f"  Total cost: ${session_data['total_cost']:.2f}")
print(f"  Total tokens: {session_data['total_tokens']:,}")
print(f"  Keys available: {list(session_data.keys())}")

# Check what Claude Monitor might be showing
print(f"\nDirect totals from data:")
print(f"  Total input tokens: {session_data.get('total_input_tokens', 0):,}")
print(f"  Total output tokens: {session_data.get('total_output_tokens', 0):,}")
print(f"  Sum of input+output: {session_data.get('total_input_tokens', 0) + session_data.get('total_output_tokens', 0):,}")

# Calculate non-cache tokens
non_cache_tokens = 0
if session_data['model_breakdown']:
    print("\nModel breakdown:")
    for model, stats in session_data['model_breakdown'].items():
        input_tokens = stats.get('input_tokens', 0)
        output_tokens = stats.get('output_tokens', 0)
        cache_creation = stats.get('cache_creation_tokens', 0)
        cache_read = stats.get('cache_read_tokens', 0)
        
        model_non_cache = input_tokens + output_tokens
        non_cache_tokens += model_non_cache
        
        print(f"  {model}:")
        print(f"    Input: {input_tokens:,}")
        print(f"    Output: {output_tokens:,}")
        print(f"    Cache creation: {cache_creation:,}")
        print(f"    Cache read: {cache_read:,}")
        print(f"    Non-cache total: {model_non_cache:,}")

print(f"\nCalculated non-cache tokens: {non_cache_tokens:,}")