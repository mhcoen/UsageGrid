"""
Enhanced Claude Code card that shows subscription and usage costs
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# No longer need session_helper since we calculate session boundaries mathematically


class ClaudeCodeCard(QFrame):
    """Claude Code card with subscription and usage display"""
    
    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.session_start_time = None
        self.current_tokens = 0
        self.token_limit = 220000  # Default
        self.recent_token_rates = []  # Track token usage rate
        self.setup_ui()
        
        # Timer to update time remaining
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self.update_time_display)
        self.time_update_timer.start(1000)  # Update every second
        
    def _load_config(self) -> dict:
        """Load configuration"""
        config_path = Path(__file__).parent.parent.parent / "config.json"
        default_config = {
            "claude_code": {
                "subscription_plan": "max20",
                "plans": {
                    "max20": {"monthly_cost": 200},
                    "max100": {"monthly_cost": 100},
                    "max200": {"monthly_cost": 200}
                }
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except:
            pass
            
        return default_config
        
    def setup_ui(self):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(220, 280)  # Taller for additional info
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(4)
        
        # Title with plan name
        plan = self.config.get("claude_code", {}).get("subscription_plan", "max20")
        
        # Simple plan name mapping
        plan_names = {
            "pro": "Pro",
            "max5": "Max5x",
            "max20": "Max20x"
        }
        plan_display = plan_names.get(plan, "Max20x")
        
        self.title_label = QLabel(f"Claude Code: {plan_display}")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #333;")
        layout.addWidget(self.title_label)
        
        # Token progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% of token limit")
        layout.addWidget(self.progress_bar)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.token_label)
        
        # Time progress bar (session duration)
        self.time_label = QLabel("Session Time")
        self.time_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 8px;")
        layout.addWidget(self.time_label)
        
        self.time_progress_bar = QProgressBar()
        self.time_progress_bar.setMaximum(100)
        self.time_progress_bar.setMinimumHeight(16)
        self.time_progress_bar.setTextVisible(True)
        self.time_progress_bar.setFormat("%p%")
        self.time_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6c757d;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.time_progress_bar)
        
        # Time remaining
        self.time_remaining_label = QLabel("Time left: -")
        self.time_remaining_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.time_remaining_label)
        
        # Prediction
        self.prediction_label = QLabel("Prediction: -")
        self.prediction_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.prediction_label)
        
        # New session info
        self.new_session_label = QLabel("")
        self.new_session_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.new_session_label)
        
        # Status
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("color: gray; margin-top: 8px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Card styling
        self.setStyleSheet("""
            ClaudeCodeCard {
                background-color: white;
                border: 2px solid #e16e3d;
                border-radius: 10px;
            }
        """)
        
    def update_display(self, daily_cost: float, session_cost: float, tokens: int, is_active: bool, 
                      session_start: datetime = None, initial_rate_data: list = None):
        """Update the display with usage data"""
        # Get token limit from config
        plan = self.config.get("claude_code", {}).get("subscription_plan", "max20")
        plans = self.config.get("claude_code", {}).get("plans", {})
        plan_info = plans.get(plan, {
            "session_token_limit": 220000
        })
        token_limit = plan_info.get("session_token_limit", 220000)
        self.token_limit = token_limit
        
        # Update session start time
        if session_start:
            self.session_start_time = session_start
        
        # Initialize rate data from historical data if provided
        if initial_rate_data and not self.recent_token_rates:
            self.recent_token_rates = initial_rate_data[-10:]  # Keep last 10
        
        # Track token usage rate
        if self.current_tokens > 0 and tokens > self.current_tokens:
            tokens_added = tokens - self.current_tokens
            self.recent_token_rates.append(tokens_added)
            # Keep only last 10 measurements
            if len(self.recent_token_rates) > 10:
                self.recent_token_rates.pop(0)
        
        self.current_tokens = tokens
        
        # Calculate token percentage
        token_percentage = (tokens / token_limit * 100) if token_limit > 0 else 0
        
        # Update progress bar based on tokens
        self.progress_bar.setValue(int(token_percentage))
        
        # Color code the progress bar based on token usage
        if token_percentage >= 90:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #dc3545;
                    border-radius: 4px;
                }
            """)  # Red
        elif token_percentage >= 75:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #ff6b35;
                    border-radius: 4px;
                }
            """)  # Orange
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #28a745;
                    border-radius: 4px;
                }
            """)  # Green
        
        # Update tokens
        if tokens > 0:
            self.token_label.setText(f"Tokens: {tokens:,} of {token_limit:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        # Update status
        if is_active:
            self.status_label.setText("Active Session")
            self.status_label.setStyleSheet("color: #28a745; margin-top: 8px;")
        else:
            self.status_label.setText("No active session")
            self.status_label.setStyleSheet("color: gray; margin-top: 8px;")
        
        # Update time display
        self.update_time_display()
        
    def update_time_display(self):
        """Update time-related displays"""
        # Use UTC time
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # If we have a session start time, use it
        if self.session_start_time:
            session_start = self.session_start_time
            # Session ends 5 hours after it starts, on the hour
            session_end = session_start + timedelta(hours=5)
        else:
            # Fallback: calculate from current time
            # Find the next hour boundary
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            # Session ends at the next hour boundary that would allow for a 5-hour session
            session_end = next_hour
            
            # Session started 5 hours before it ends
            session_start = session_end - timedelta(hours=5)
        
        # Calculate remaining and elapsed time
        remaining = session_end - now
        elapsed = now - session_start
        
        # Calculate time percentage
        session_duration = timedelta(hours=5)
        time_percentage = (elapsed.total_seconds() / session_duration.total_seconds() * 100)
        time_percentage = min(100, max(0, time_percentage))
        
        # Update time progress bar
        self.time_progress_bar.setValue(int(time_percentage))
        
        # Format time remaining (without seconds)
        if remaining.total_seconds() > 0:
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            self.time_remaining_label.setText(f"Time left: {hours}h {minutes}m")
        else:
            self.time_remaining_label.setText("Time left: Session expired")
        
        # Calculate prediction
        if self.recent_token_rates and remaining.total_seconds() > 0:
            # Average tokens per update (every 30 seconds)
            avg_rate = sum(self.recent_token_rates) / len(self.recent_token_rates)
            
            # Calculate when we'll hit the limit
            if avg_rate > 0:
                tokens_until_limit = self.token_limit - self.current_tokens
                updates_until_limit = tokens_until_limit / avg_rate
                time_until_limit = timedelta(seconds=updates_until_limit * 30)
                
                # Calculate the exact time when tokens will run out
                limit_time = now + time_until_limit
                
                # Format time like Claude Monitor (local time)
                # Convert from UTC to local time for display
                from zoneinfo import ZoneInfo
                utc_time = limit_time.replace(tzinfo=ZoneInfo('UTC'))
                local_limit_time = utc_time.astimezone()
                time_str = local_limit_time.strftime("%I:%M %p").lstrip('0')
                
                # Always show the time tokens will run out
                if time_until_limit < remaining:
                    # Will run out before session ends
                    self.prediction_label.setText(f"Tokens will run out: {time_str}")
                    self.prediction_label.setStyleSheet("color: #ff6b35; font-size: 11px; font-weight: bold;")
                else:
                    # Will run out after session ends
                    self.prediction_label.setText(f"Tokens will run out: {time_str}")
                    self.prediction_label.setStyleSheet("color: #28a745; font-size: 11px;")
            else:
                self.prediction_label.setText("Rate: Stable")
                self.prediction_label.setStyleSheet("color: #666; font-size: 11px;")
        else:
            self.prediction_label.setText("Prediction: Calculating...")
            self.prediction_label.setStyleSheet("color: #666; font-size: 11px;")
            
        # Always show when new session starts
        # Convert session_end (UTC) to local time for display
        from zoneinfo import ZoneInfo
        utc_session_end = session_end.replace(tzinfo=ZoneInfo('UTC'))
        local_session_end = utc_session_end.astimezone()
        new_session_time = local_session_end.strftime("%I:%M %p").lstrip('0')
        self.new_session_label.setText(f"New session starts: {new_session_time}")