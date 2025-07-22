"""
Enhanced Claude Code card that shows subscription and usage costs
"""
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from PyQt6.QtWidgets import QLabel, QProgressBar, QFrame, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from .base_card import BaseProviderCard

logger = logging.getLogger(__name__)


class ModelUsageGraph(QWidget):
    """Horizontal bar showing Opus 4 vs Sonnet 4 usage percentage"""
    
    def __init__(self):
        super().__init__()
        self.opus_percentage = 50.0  # Default to 50/50
        self.setMinimumHeight(10)
        self.setMaximumHeight(12)
        
    def set_data(self, model_breakdown: Dict[str, Any]):
        """Update graph with model usage data"""
        # Calculate percentages from total session usage
        opus_tokens = 0
        sonnet_tokens = 0
        
        for model, stats in model_breakdown.items():
            total_tokens = stats.get('input_tokens', 0) + stats.get('output_tokens', 0)
            if 'opus' in model.lower():
                opus_tokens += total_tokens
            elif 'sonnet' in model.lower():
                sonnet_tokens += total_tokens
                
        total = opus_tokens + sonnet_tokens
        if total > 0:
            self.opus_percentage = (opus_tokens / total) * 100
        else:
            self.opus_percentage = 50.0
            
        self.update()
            
    def paintEvent(self, event):
        """Paint the horizontal percentage bar"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(230, 230, 230))
        
        # Calculate split point
        width = self.width()
        split_x = int(width * self.opus_percentage / 100)
        
        # Draw Opus portion (blue)
        if split_x > 0:
            painter.fillRect(0, 0, split_x, self.height(), QColor(41, 98, 255))
        
        # Draw Sonnet portion (orange) 
        if split_x < width:
            painter.fillRect(split_x, 0, width - split_x, self.height(), QColor(255, 106, 53))


class ClaudeCodeCard(BaseProviderCard):
    """Claude Code card with subscription and usage display"""
    
    def __init__(self):
        self.config = self._load_config()
        self.session_start_time = None
        self.current_tokens = 0
        self.token_limit = 220000  # Default
        self.recent_token_rates = []  # Track token usage rate
        
        # Get plan name for display
        plan = self.config.get("claude_code", {}).get("subscription_plan", "max20")
        plan_names = {
            "pro": "Pro",
            "max5": "Max5x",
            "max20": "Max20x"
        }
        plan_display = plan_names.get(plan, "Max20x")
        
        super().__init__(
            provider_name="anthropic",
            display_name=f"Claude Code: {plan_display}",
            color="#ff6b35"  # Vibrant orange
        )
        self.billing_url = "https://console.anthropic.com/settings/billing"
        self.enable_billing_link()
        # Update every 30 seconds
        self.update_interval = 30000
        
        # Theme colors
        self.progress_bar_bg = "#e0e0e0"
        self.progress_bar_text = "#000000"
        self.time_bar_bg = "#e0e0e0"
        self.time_bar_chunk = "#6c757d"
        
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
        
    def get_font_size(self) -> int:
        """Get current font size for dynamic text"""
        # Check if parent window has font scale
        parent = self.window()
        if parent and hasattr(parent, 'font_scale'):
            return int(self.base_font_sizes['small'] * parent.font_scale)
        return self.base_font_sizes['small']
        
    def setup_content(self):
        """Setup Claude Code specific content"""
        
        # Group all graphs together with same height
        
        # 1. Token progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimumHeight(10)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% of token limit")
        self.layout.addWidget(self.progress_bar)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet(f"font-size: {self.base_font_sizes['secondary'] - 1}px;")
        self.layout.addWidget(self.token_label)
        
        # 2. Session time progress bar
        self.time_label = QLabel("Session Time")
        self.time_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px; margin-top: 2px;")
        self.layout.addWidget(self.time_label)
        
        self.time_progress_bar = QProgressBar()
        self.time_progress_bar.setMaximum(100)
        self.time_progress_bar.setMinimumHeight(10)
        self.time_progress_bar.setMaximumHeight(12)
        self.time_progress_bar.setTextVisible(True)
        self.time_progress_bar.setFormat("%p%")
        # Initial styling will be set by theme
        self.layout.addWidget(self.time_progress_bar)
        
        # Time remaining (right after session time bar)
        self.time_remaining_label = QLabel("Time left: -")
        self.time_remaining_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        self.layout.addWidget(self.time_remaining_label)
        
        # 3. Model usage horizontal bar
        self.model_label = QLabel("Model Usage")
        self.model_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px; margin-top: 2px;")
        self.layout.addWidget(self.model_label)
        
        self.model_graph = ModelUsageGraph()
        self.layout.addWidget(self.model_graph)
        
        # Model legend
        self.model_legend = QLabel('<span style="color: #2962FF;">■ Opus</span>  <span style="color: #FF6A35;">■ Sonnet</span>')
        self.model_legend.setTextFormat(Qt.TextFormat.RichText)
        self.model_legend.setStyleSheet(f"font-size: {self.base_font_sizes['small'] - 1}px;")
        self.layout.addWidget(self.model_legend)
        
        # Prediction
        self.prediction_label = QLabel("Prediction: -")
        self.prediction_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        self.layout.addWidget(self.prediction_label)
        
        # New session info
        self.new_session_label = QLabel("")
        self.new_session_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        self.layout.addWidget(self.new_session_label)
        
    def update_display(self, data: Dict[str, Any]):
        """Update the display with usage data"""
        # Extract data
        daily_cost = data.get('daily_cost', 0.0)
        session_cost = data.get('session_cost', 0.0)
        tokens = data.get('tokens', 0)
        is_active = data.get('is_active', False)
        session_start = data.get('session_start')
        initial_rate_data = data.get('initial_rate_data', [])
        model_breakdown = data.get('model_breakdown', {})
        
        # Debug logging
        logger.debug(f"ClaudeCodeCard.update_display called with tokens={tokens}, session_cost=${session_cost:.4f}")
        # Get token limit from config
        plan = self.config.get("claude_code", {}).get("subscription_plan", "max20")
        plans = self.config.get("claude_code", {}).get("plans", {})
        plan_info = plans.get(plan, {
            "session_token_limit": 220000
        })
        token_limit = plan_info.get("session_token_limit", 220000)
        self.token_limit = token_limit
        
        logger.debug(f"Token limit: {token_limit}, current tokens: {tokens}, percentage: {(tokens / token_limit * 100) if token_limit > 0 else 0:.1f}%")
        
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
        
        # Update progress bar based on tokens (cap at 100%)
        self.progress_bar.setValue(min(100, int(token_percentage)))
        
        # Update progress bar format based on whether we're over limit
        if token_percentage > 100:
            self.progress_bar.setFormat(f"{int(token_percentage)}% of token limit")
        else:
            self.progress_bar.setFormat("%p% of token limit")
        
        # Color code the progress bar based on token usage
        self._update_progress_bar_color(token_percentage)
        
        # Update tokens
        if tokens > 0:
            self.token_label.setText(f"Tokens: {tokens:,} of {token_limit:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        # Update status
        if is_active:
            self.update_status("Active Session", "active")
        else:
            self.update_status("No active session", "normal")
        
        # Update time display
        self.update_time_display()
        
        # Update model usage graph
        if model_breakdown:
            self.model_graph.set_data(model_breakdown)
        
    def update_time_display(self):
        """Update time-related displays"""
        # Use UTC time for calculations
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Use the actual session start time from the data
        if self.session_start_time:
            session_start = self.session_start_time
        else:
            # Fall back to finding session start from JSONL data
            from ...utils.session_helper import find_session_start
            session_start = find_session_start(now)
        
        session_end = session_start + timedelta(hours=5)
        
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
                    self.prediction_label.setStyleSheet(f"color: #ff6b35; font-size: {self.get_font_size()}px; font-weight: bold;")
                else:
                    # Will run out after session ends
                    self.prediction_label.setText(f"Tokens will run out: {time_str}")
                    self.prediction_label.setStyleSheet(f"color: #28a745; font-size: {self.get_font_size()}px;")
            else:
                self.prediction_label.setText("Rate: Stable")
                self.prediction_label.setStyleSheet(f" font-size: {self.get_font_size()}px;")
        else:
            self.prediction_label.setText("Prediction: Calculating...")
            self.prediction_label.setStyleSheet(" font-size: 11px;")
            
        # Show when the next session starts (after current session ends)
        # Convert session_end (UTC) to local time for display
        from zoneinfo import ZoneInfo
        utc_session_end = session_end.replace(tzinfo=ZoneInfo('UTC'))
        local_session_end = utc_session_end.astimezone()
        new_session_time = local_session_end.strftime("%I:%M %p").lstrip('0')
        # Next session starts immediately when current one ends
        self.new_session_label.setText(f"Next session: {new_session_time}")
        
    def scale_content_fonts(self, scale: float):
        """Scale Claude Code specific fonts"""
        # Scale token label (1pt smaller than secondary)
        self.token_label.setStyleSheet(f" font-size: {int((self.base_font_sizes['secondary'] - 1) * scale)}px;")
        
        # Scale time labels
        self.time_label.setStyleSheet(f" font-size: {int(self.base_font_sizes['small'] * scale)}px; margin-top: 2px;")
        self.time_remaining_label.setStyleSheet(f" font-size: {int(self.base_font_sizes['small'] * scale)}px;")
        self.new_session_label.setStyleSheet(f" font-size: {int(self.base_font_sizes['small'] * scale)}px;")
        self.model_label.setStyleSheet(f" font-size: {int(self.base_font_sizes['small'] * scale)}px; margin-top: 2px;")
        self.model_legend.setStyleSheet(f"font-size: {int((self.base_font_sizes['small'] - 1) * scale)}px;")
        
        # Scale prediction label with special handling for its dynamic styling
        current_style = self.prediction_label.styleSheet()
        if "color: #ff6b35" in current_style:  # Orange warning
            self.prediction_label.setStyleSheet(f"color: #ff6b35; font-size: {int(self.base_font_sizes['small'] * scale)}px; font-weight: bold;")
        elif "color: #28a745" in current_style:  # Green
            self.prediction_label.setStyleSheet(f"color: #28a745; font-size: {int(self.base_font_sizes['small'] * scale)}px;")
        else:  # Default
            self.prediction_label.setStyleSheet(f" font-size: {int(self.base_font_sizes['small'] * scale)}px;")
            
    def update_theme_colors(self, is_dark: bool):
        """Update progress bar colors based on theme"""
        if is_dark:
            # Dark theme - use lighter backgrounds and white text
            self.progress_bar_bg = "#404040"
            self.progress_bar_text = "#ffffff"
            self.time_bar_bg = "#404040"
            self.time_bar_chunk = "#808080"
        else:
            # Light theme - use darker text on light backgrounds
            self.progress_bar_bg = "#e0e0e0"
            self.progress_bar_text = "#000000"
            self.time_bar_bg = "#e0e0e0"
            self.time_bar_chunk = "#6c757d"
            
        # Update time progress bar
        self.time_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.time_bar_bg};
                text-align: center;
                color: {self.progress_bar_text};
                font-size: {self.base_font_sizes['small'] - 1}px;
            }}
            QProgressBar::chunk {{
                background-color: {self.time_bar_chunk};
            }}
        """)
        
        # Re-apply token progress bar color with theme
        if hasattr(self, 'current_tokens'):
            token_percentage = (self.current_tokens / self.token_limit * 100) if self.token_limit > 0 else 0
            self._update_progress_bar_color(token_percentage)
            
    def _update_progress_bar_color(self, token_percentage: float):
        """Update progress bar color based on percentage"""
        if token_percentage >= 90:
            chunk_color = "#dc3545"  # Red
        elif token_percentage >= 75:
            chunk_color = "#ff6b35"  # Orange
        else:
            chunk_color = "#28a745"  # Green
            
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.progress_bar_bg};
                text-align: center;
                color: {self.progress_bar_text};
                font-size: {self.base_font_sizes['small'] - 1}px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
            }}
        """)