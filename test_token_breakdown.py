#!/usr/bin/env python3
"""Debug token counting"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

reader = ClaudeCodeReader()

# Get 1 hour of data
now = datetime.utcnow()
one_hour_ago = now - timedelta(hours=1)
data = reader.get_usage_data(since_date=one_hour_ago)

print("Claude Code Token Breakdown (last 1 hour):")
print("-" * 50)
print(f"Total Cost: ${data['total_cost']:.2f}")
print(f"Total Tokens (all types): {data['total_tokens']:,}")
print(f"  Input Tokens: {data['total_input_tokens']:,}")
print(f"  Output Tokens: {data['total_output_tokens']:,}")
print()

# Check model breakdown
if data['model_breakdown']:
    print("Token breakdown by type:")
    for model, stats in data['model_breakdown'].items():
        if stats['cost'] > 0:
            print(f"\n{model}:")
            print(f"  Input tokens: {stats.get('input_tokens', 0):,}")
            print(f"  Cache creation: {stats.get('cache_creation_tokens', 0):,}")
            print(f"  Cache read: {stats.get('cache_read_tokens', 0):,}")
            print(f"  Output tokens: {stats.get('output_tokens', 0):,}")
            
            # Calculate non-cache tokens
            non_cache = stats.get('input_tokens', 0) + stats.get('output_tokens', 0)
            print(f"  Non-cache tokens: {non_cache:,}")

# Calculate totals without cache
total_non_cache = 0
for model, stats in data['model_breakdown'].items():
    total_non_cache += stats.get('input_tokens', 0) + stats.get('output_tokens', 0)
    
print(f"\nTotal non-cache tokens (input + output only): {total_non_cache:,}")
print(f"This might be closer to the expected 26,247")