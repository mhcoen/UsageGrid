#!/usr/bin/env python3
"""Debug Claude Code sessions"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.claude_code_reader import ClaudeCodeReader
from datetime import datetime, timedelta

reader = ClaudeCodeReader()

# Check different time windows
print("Claude Code Usage by Time Window:")
print("-" * 50)

for hours in [1, 5, 24, 96, 192]:
    since = datetime.utcnow() - timedelta(hours=hours)
    data = reader.get_usage_data(since_date=since)
    
    print(f"\nLast {hours} hours:")
    print(f"  Cost: ${data['total_cost']:.2f}")
    print(f"  Tokens: {data['total_tokens']:,}")
    print(f"  Messages: {data.get('session_count', 0)}")
    
    if data['model_breakdown']:
        models = list(data['model_breakdown'].keys())
        if models:
            print(f"  Models: {', '.join(models[:2])}")