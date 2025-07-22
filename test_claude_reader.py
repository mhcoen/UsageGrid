#!/usr/bin/env python3
"""Test Claude Code reader"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

reader = ClaudeCodeReader()

# Try different time ranges
print("Testing Claude Code reader...")

# Last 7 days
since = datetime.utcnow() - timedelta(days=7)
data = reader.get_usage_data(since_date=since)
print(f"\nLast 7 days:")
print(f"  Cost: ${data['total_cost']:.4f}")
print(f"  Tokens: {data['total_tokens']:,}")
print(f"  Models: {list(data['model_breakdown'].keys())[:3] if data['model_breakdown'] else 'None'}")

# All time (no date filter)
data = reader.get_usage_data(since_date=None)
print(f"\nAll time (no date filter):")
print(f"  Cost: ${data['total_cost']:.4f}")
print(f"  Tokens: {data['total_tokens']:,}")
print(f"  Models: {list(data['model_breakdown'].keys())[:3] if data['model_breakdown'] else 'None'}")