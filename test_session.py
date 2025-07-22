#!/usr/bin/env python3
"""Test session detection logic"""
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.session_helper import get_current_session_start

# Current time
now = datetime.now(timezone.utc).replace(tzinfo=None)
print(f"Current time: {now}")

# Get session start
session_start = get_current_session_start(now)
print(f"Session started: {session_start}")
print(f"Hours ago: {(now - session_start).total_seconds() / 3600:.1f}")

# Test different times
print("\nTesting session boundaries:")
test_times = [
    datetime(2025, 7, 20, 0, 30),   # 00:30 - in first session
    datetime(2025, 7, 20, 4, 59),   # 04:59 - end of first session  
    datetime(2025, 7, 20, 5, 0),    # 05:00 - start of second session
    datetime(2025, 7, 20, 12, 30),  # 12:30 - in third session
    datetime(2025, 7, 20, 20, 30),  # 20:30 - in fifth session
    datetime(2025, 7, 20, 23, 59),  # 23:59 - still in fifth session
]

for test_time in test_times:
    start = get_current_session_start(test_time)
    hours = (test_time - start).total_seconds() / 3600
    print(f"{test_time.strftime('%H:%M')} -> Session start: {start.strftime('%H:%M')} ({hours:.1f} hours in)")