#!/usr/bin/env python3
"""Test the updated Claude Code reader"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

reader = ClaudeCodeReader()

# Test with 96 hour window (like Claude Monitor)
since = datetime.utcnow() - timedelta(hours=96)
data = reader.get_usage_data(since_date=since)

print(f"Claude Code Usage (last 96 hours):")
print(f"  Total Cost: ${data['total_cost']:.2f}")
print(f"  Total Tokens: {data['total_tokens']:,}")
print(f"  Total Input Tokens: {data['total_input_tokens']:,}")
print(f"  Total Output Tokens: {data['total_output_tokens']:,}")
print(f"  Files Processed: {data['file_count']}")
print(f"  Sessions: {data['session_count']}")

if data['model_breakdown']:
    print(f"\nModel Breakdown:")
    for model, stats in data['model_breakdown'].items():
        print(f"  {model}:")
        print(f"    Cost: ${stats['cost']:.2f}")
        print(f"    Requests: {stats['requests']}")
        print(f"    Input Tokens: {stats.get('input_tokens', 0):,}")
        print(f"    Cache Creation: {stats.get('cache_creation_tokens', 0):,}")
        print(f"    Cache Read: {stats.get('cache_read_tokens', 0):,}")
        print(f"    Output Tokens: {stats.get('output_tokens', 0):,}")