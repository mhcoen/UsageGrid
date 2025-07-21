#!/usr/bin/env python3
"""
Lightweight version with minimal processing to avoid locking up
"""
import sys
import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import threading

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.providers.claude_code_reader import ClaudeCodeReader
from src.ui.claude_code_card import ClaudeCodeCard
from src.ui.openai_card import OpenAICard
from src.ui.openrouter_card import OpenRouterCard
from src.utils.session_helper import find_session_start
from src.core.cache_db import CacheDB

# Setup logging to file
log_file = '/tmp/llm_monitor.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Reduce verbosity of Claude reader logs
logging.getLogger('src.providers.claude_code_reader').setLevel(logging.WARNING)


class SimpleProviderCard(QFrame):
    """Simple provider card widget"""
    
    def __init__(self, provider_name: str, display_name: str, color: str):
        super().__init__()
        self.provider_name = provider_name
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(220, 160)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Provider name
        self.name_label = QLabel(display_name)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        self.name_label.setStyleSheet("color: #333;")
        layout.addWidget(self.name_label)
        
        # Cost display
        self.cost_label = QLabel("$0.00")
        font = QFont()
        font.setPointSize(20)
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; font-weight: bold;")
        layout.addWidget(self.cost_label)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet("color: #666;")
        layout.addWidget(self.token_label)
        
        # Status
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet(f"""
            SimpleProviderCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
            }}
        """)
        
    def update_display(self, cost: float, tokens: Optional[int], status: str):
        """Update the card display"""
        # Always show 4 decimal places for daily cost
        self.cost_label.setText(f"${cost:.4f}")
        
        if tokens is not None:
            self.token_label.setText(f"Tokens: {tokens:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        self.status_label.setText(status)
        
        # Update status color
        if status == "Active" or "Session" in status:
            self.status_label.setStyleSheet("color: #28a745;")
        elif "Error" in status:
            self.status_label.setStyleSheet("color: #dc3545;")
        else:
            self.status_label.setStyleSheet("color: gray;")


class ClaudeDataWorker(QObject):
    """Worker to fetch Claude data in background thread"""
    data_ready = pyqtSignal(dict)
    
    def __init__(self, claude_reader):
        super().__init__()
        self.claude_reader = claude_reader
        self._thread = None
        self._stop_flag = threading.Event()
        
    def fetch_data_async(self, session_start: datetime, now: datetime):
        """Start fetching data in a background thread"""
        # Don't start a new thread if one is already running
        if self._thread and self._thread.is_alive():
            logger.debug("Claude fetch already in progress, skipping")
            return
            
        # Start new thread
        self._thread = threading.Thread(
            target=self._fetch_data_thread, 
            args=(session_start, now),
            daemon=True
        )
        self._thread.start()
        
    def _fetch_data_thread(self, session_start: datetime, now: datetime):
        """Thread function to fetch data"""
        try:
            logger.debug("Starting Claude data fetch in background")
            
            # Get session data
            session_data = self.claude_reader.get_usage_data(since_date=session_start)
            
            # Get daily data
            one_day_ago = now - timedelta(hours=24)
            daily_data = self.claude_reader.get_usage_data(since_date=one_day_ago)
            
            # Calculate non-cache tokens
            non_cache_tokens = 0
            if session_data['model_breakdown']:
                for model_stats in session_data['model_breakdown'].values():
                    non_cache_tokens += model_stats.get('input_tokens', 0)
                    non_cache_tokens += model_stats.get('output_tokens', 0)
            
            # Get rate history
            rate_history = self.claude_reader.get_token_rate_history(session_start, interval_minutes=0.5)
            
            result = {
                'daily': daily_data['total_cost'],
                'session': session_data['total_cost'],
                'tokens': non_cache_tokens,
                'session_start': session_start,
                'rate_history': rate_history,
                'success': True
            }
            
            # Emit result back to main thread
            self.data_ready.emit(result)
            
        except Exception as e:
            logger.error(f"Error in background Claude fetch: {e}")
            self.data_ready.emit({
                'daily': 0.0,
                'session': 0.0,
                'tokens': 0,
                'session_start': None,
                'rate_history': [],
                'success': False
            })
            
    def stop(self):
        """Stop the worker thread"""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=1.0)


class LiteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.provider_cards = {}
        self.api_keys = {}
        self.update_timer = None
        self.claude_update_timer = None  # Separate timer for Claude
        self.claude_reader = ClaudeCodeReader()  # Initialize once
        self.claude_worker = ClaudeDataWorker(self.claude_reader)
        self.claude_worker.data_ready.connect(self.on_claude_data_ready)
        self.claude_fetch_in_progress = False
        self.last_claude_update = None
        self.cached_claude_data = {'daily': 0.0, 'session': 0.0, 'tokens': 0, 'session_start': None, 'rate_history': []}
        self.daily_totals = {}  # Track daily costs for all providers
        self.monthly_totals = {}  # Track monthly costs for all providers
        self.cached_provider_data = {}  # Cache last known values for each provider
        self.openai_weekly_data = {}  # Cache weekly data for OpenAI
        self.config = self._load_config()
        self.cache_db = CacheDB()  # Initialize cache database
        
        self.load_api_keys()
        self.setup_ui()
        self.setup_providers()
        self.start_updates()
        
    def load_api_keys(self):
        """Load API keys from environment"""
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        }
        
    def _load_config(self) -> dict:
        """Load configuration"""
        import json
        from pathlib import Path
        config_path = Path(__file__).parent.parent / "config.json"
        default_config = {
            "claude_code": {
                "subscription_plan": "max20",
                "plans": {
                    "max20": {"monthly_cost": 20},
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
        
    def get_claude_subscription_cost(self) -> int:
        """Get monthly subscription cost for Claude Code"""
        plan = self.config.get("claude_code", {}).get("subscription_plan", "max20")
        plans = self.config.get("claude_code", {}).get("plans", {})
        return plans.get(plan, {}).get("monthly_cost", 0)
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("LLM Cost Monitor - Lite")
        self.setMinimumSize(900, 650)
        
        # Make window closeable
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("LLM Cost Monitor")
        font = QFont()
        font.setPointSize(26)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Totals section
        totals_layout = QVBoxLayout()
        
        self.daily_total_label = QLabel("Daily: $0.00")
        font = QFont()
        font.setPointSize(14)
        self.daily_total_label.setFont(font)
        totals_layout.addWidget(self.daily_total_label)
        
        self.monthly_total_label = QLabel("Subscriptions: $0/mo")
        font = QFont()
        font.setPointSize(14)
        self.monthly_total_label.setFont(font)
        totals_layout.addWidget(self.monthly_total_label)
        
        header_layout.addLayout(totals_layout)
        
        layout.addLayout(header_layout)
        
        # Info bar
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Fetching real API data...")
        self.info_label.setStyleSheet("color: #666; padding: 10px;")
        info_layout.addWidget(self.info_label)
        
        self.last_update_label = QLabel("Last update: Never")
        self.last_update_label.setStyleSheet("color: #666; padding: 10px;")
        info_layout.addStretch()
        info_layout.addWidget(self.last_update_label)
        
        layout.addLayout(info_layout)
        
        # Provider grid
        self.provider_grid = QGridLayout()
        self.provider_grid.setSpacing(20)
        layout.addLayout(self.provider_grid)
        
        layout.addStretch()
        
        # Status bar
        self.statusBar().showMessage("Initializing...")
        
        central_widget.setLayout(layout)
        
    def setup_providers(self):
        """Setup provider cards"""
        # OpenAI - top left (enhanced card)
        openai_card = OpenAICard()
        openai_card.clicked.connect(self.on_provider_clicked)
        self.provider_grid.addWidget(openai_card, 0, 0)
        self.provider_cards["openai"] = openai_card
        
        # Claude Code - top right (special card)
        claude_card = ClaudeCodeCard()
        self.provider_grid.addWidget(claude_card, 0, 1)
        self.provider_cards["anthropic"] = claude_card
        
        # OpenRouter - bottom left
        openrouter_card = OpenRouterCard()
        self.provider_grid.addWidget(openrouter_card, 1, 0)
        self.provider_cards["openrouter"] = openrouter_card
        
        # Gemini - bottom right
        gemini_card = SimpleProviderCard("gemini", "Gemini", "#4285f4")
        self.provider_grid.addWidget(gemini_card, 1, 1)
        self.provider_cards["gemini"] = gemini_card
            
    def start_updates(self):
        """Start the update timers"""
        # Timer for API providers (5 minutes)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.fetch_api_providers)
        self.update_timer.start(300000)  # Update every 5 minutes
        
        # Timer for Claude Code (30 seconds)
        self.claude_update_timer = QTimer()
        self.claude_update_timer.timeout.connect(self.update_claude_only)
        self.claude_update_timer.start(30000)  # Update every 30 seconds
        
        # Initial fetch
        self.fetch_all_data()
        
    def fetch_all_data(self):
        """Fetch data from all providers"""
        try:
            # Reset totals
            daily_usage_total = 0.0  # Only pay-per-use services
            subscription_total = 0.0  # Only subscriptions
            
            # OpenAI - pay-per-use (add to daily total)
            if self.api_keys["openai"]:
                cost, tokens = self.fetch_openai_data()
                if cost == -429:  # Rate limited
                    cached = self.cached_provider_data.get("openai", {"cost": 0.0, "tokens": None})
                    self.provider_cards["openai"].update_display(
                        cached["cost"], cached["tokens"], 
                        "Waiting for API reset"
                    )
                    daily_usage_total += cached["cost"]
                elif cost >= 0:  # Valid response (including 0)
                    self.cached_provider_data["openai"] = {"cost": cost, "tokens": tokens}
                    self.provider_cards["openai"].update_display(cost, tokens, "Active" if cost > 0 else "No usage today")
                    daily_usage_total += cost
                    
                    # Fetch weekly data if we don't have it yet or it's been a while
                    if not self.openai_weekly_data or cost > 0:
                        weekly_data = self.fetch_openai_weekly_data()
                        if weekly_data:
                            self.openai_weekly_data = weekly_data
                            self.provider_cards["openai"].update_weekly_data(weekly_data)
                else:  # Other error occurred
                    cached = self.cached_provider_data.get("openai", {"cost": 0.0, "tokens": None})
                    self.provider_cards["openai"].update_display(
                        cached["cost"], cached["tokens"], 
                        "API error"
                    )
                    daily_usage_total += cached["cost"]
            else:
                self.provider_cards["openai"].update_display(0.0, None, "No API key")
                
            # OpenRouter - pay-per-use (add to daily total)
            if self.api_keys["openrouter"]:
                openrouter_data = self.fetch_openrouter_data()
                cost = openrouter_data.get("usage", 0.0)
                
                # Build status string
                status = "Active" if cost > 0 else "No usage"
                self.provider_cards["openrouter"].update_display(cost, None, status)
                
                # Update detailed info
                if hasattr(self.provider_cards["openrouter"], "update_detailed_info"):
                    self.provider_cards["openrouter"].update_detailed_info(openrouter_data)
                
                # Note: OpenRouter shows total balance used, we'd need more logic for daily
                # For now, exclude from daily total or add logic to track daily changes
            else:
                self.provider_cards["openrouter"].update_display(0.0, None, "No API key")
                
            # Claude Code - subscription service (NOT in daily total)
            # This will either return cached data or trigger a background update
            claude_data = self.fetch_claude_code_cached()
            if claude_data['tokens'] > 0:  # Only update if we have data
                session_start = claude_data.get('session_start')
                rate_history = claude_data.get('rate_history', [])
                
                self.provider_cards["anthropic"].update_display(
                    claude_data['daily'], 
                    claude_data['session'], 
                    claude_data['tokens'],
                    claude_data['session'] > 0,
                    session_start,
                    rate_history
                )
            # Get subscription cost from config
            subscription_total = self.get_claude_subscription_cost()
                
            # Gemini - pay-per-use
            if self.api_keys["gemini"]:
                cost = self.fetch_gemini_data()
                if cost >= 0:
                    self.cached_provider_data["gemini"] = {"cost": cost, "tokens": None}
                    self.provider_cards["gemini"].update_display(cost, None, "Active" if cost > 0 else "No usage")
                    daily_usage_total += cost
                else:
                    # Show appropriate status for unimplemented API
                    self.provider_cards["gemini"].update_display(0.0, None, "Cloud API needed")
            else:
                self.provider_cards["gemini"].update_display(0.0, None, "No API key")
                
            # Update totals display
            self.daily_total_label.setText(f"Daily: ${daily_usage_total:.4f}")
            self.monthly_total_label.setText(f"Subscriptions: ${subscription_total}/mo")
            self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            self.statusBar().showMessage("Data updated successfully")
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            self.statusBar().showMessage(f"Error: {str(e)[:50]}")
        
    def on_claude_data_ready(self, data: dict):
        """Handle Claude data from background thread"""
        self.claude_fetch_in_progress = False
        
        if data['success']:
            self.cached_claude_data = data
            self.last_claude_update = datetime.now(timezone.utc).replace(tzinfo=None)
            
            # Update the Claude card
            self.provider_cards["anthropic"].update_display(
                data['daily'], 
                data['session'], 
                data['tokens'],
                data['session'] > 0,
                data['session_start'],
                data['rate_history']
            )
            
            # Update totals
            self.update_totals_display()
            
            # Log the update
            if data['session_start']:
                hours_in_session = (datetime.now(timezone.utc).replace(tzinfo=None) - data['session_start']).total_seconds() / 3600
                logger.info(f"Claude Code - Session started {hours_in_session:.1f}h ago, "
                           f"Daily: ${data['daily']:.2f}, "
                           f"Session: ${data['session']:.2f}, "
                           f"Tokens: {data['tokens']:,}")
                           
            self.statusBar().showMessage("Claude data updated")
        else:
            logger.warning("Claude data fetch failed, using cached data")
            
    def fetch_claude_code_cached(self) -> dict:
        """Fetch Claude Code data with caching and background thread"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Return cached data immediately
        if self.cached_claude_data['tokens'] > 0:
            # If a fetch is not already in progress and it's been > 30 seconds, start background fetch
            if not self.claude_fetch_in_progress and (not self.last_claude_update or (now - self.last_claude_update).seconds >= 30):
                self.claude_fetch_in_progress = True
                session_start = find_session_start(now)
                self.claude_worker.fetch_data_async(session_start, now)
                self.statusBar().showMessage("Updating Claude data...")
            return self.cached_claude_data
        
        # First time - do synchronous fetch to get initial data
        try:
            session_start = find_session_start(now)
            session_data = self.claude_reader.get_usage_data(since_date=session_start)
            one_day_ago = now - timedelta(hours=24)
            daily_data = self.claude_reader.get_usage_data(since_date=one_day_ago)
            
            non_cache_tokens = 0
            if session_data['model_breakdown']:
                for model_stats in session_data['model_breakdown'].values():
                    non_cache_tokens += model_stats.get('input_tokens', 0)
                    non_cache_tokens += model_stats.get('output_tokens', 0)
            
            rate_history = self.claude_reader.get_token_rate_history(session_start, interval_minutes=0.5)
            
            self.cached_claude_data = {
                'daily': daily_data['total_cost'],
                'session': session_data['total_cost'],
                'tokens': non_cache_tokens,
                'session_start': session_start,
                'rate_history': rate_history
            }
            self.last_claude_update = now
            return self.cached_claude_data
            
        except Exception as e:
            logger.error(f"Error reading Claude Code: {e}")
            return {'daily': 0.0, 'session': 0.0, 'tokens': 0, 'session_start': None, 'rate_history': []}
        
    def fetch_openai_weekly_data(self) -> dict:
        """Fetch OpenAI usage data for the past week with caching"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "Content-Type": "application/json"
            }
            
            weekly_data = {}
            today = datetime.now(timezone.utc).date()
            
            # First, get all cached data
            cached_weekly = self.cache_db.get_openai_weekly_usage(datetime.now(timezone.utc))
            weekly_data.update(cached_weekly)
            
            # Model pricing (per 1M tokens)
            pricing = {
                "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
                "gpt-4": {"input": 30.0, "output": 60.0},
                "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            }
            
            # Only fetch data for dates we don't have cached or need to refresh
            for i in range(7):
                date = today - timedelta(days=i)
                date_str = date.isoformat()
                
                # Check if we should fetch this date
                if not self.cache_db.should_refresh_date(date_str):
                    logger.debug(f"Using cached data for {date_str}")
                    continue
                    
                try:
                    logger.info(f"Fetching OpenAI data for {date_str}")
                    response = requests.get(
                        f"https://api.openai.com/v1/usage?date={date_str}",
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        daily_tokens = 0
                        daily_cost = 0.0
                        
                        if "data" in data:
                            for item in data["data"]:
                                context_tokens = item.get("n_context_tokens_total", 0)
                                generated_tokens = item.get("n_generated_tokens_total", 0)
                                model = item.get("snapshot_id", "")
                                
                                # Get pricing
                                model_pricing = pricing.get(model, pricing["gpt-4o-mini-2024-07-18"])
                                
                                # Calculate cost
                                input_cost = (context_tokens / 1_000_000) * model_pricing["input"]
                                output_cost = (generated_tokens / 1_000_000) * model_pricing["output"]
                                
                                daily_cost += input_cost + output_cost
                                daily_tokens += context_tokens + generated_tokens
                        
                        # Cache the result
                        self.cache_db.set_openai_daily_usage(date_str, daily_tokens, daily_cost, data)
                        weekly_data[date_str] = {"tokens": daily_tokens, "cost": daily_cost}
                        
                    elif response.status_code == 429:
                        # Rate limited - stop trying to fetch more dates
                        logger.warning(f"OpenAI API rate limited on date {date_str}")
                        break
                    else:
                        # API error - don't cache, will retry next time
                        logger.error(f"OpenAI API error {response.status_code} for {date_str}")
                        if date_str not in weekly_data:
                            weekly_data[date_str] = {"tokens": 0, "cost": 0.0}
                        
                except Exception as e:
                    logger.error(f"Error fetching OpenAI data for {date_str}: {e}")
                    if date_str not in weekly_data:
                        weekly_data[date_str] = {"tokens": 0, "cost": 0.0}
                    
            return weekly_data
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI weekly data: {e}")
            return {}
    
    def fetch_openai_data(self) -> tuple[float, int]:
        """Fetch OpenAI usage data for today"""
        try:
            # Get today's date
            today = datetime.now(timezone.utc).date().isoformat()
            
            # Always fetch fresh data for today
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"https://api.openai.com/v1/usage?date={today}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                total_cost = 0.0
                total_tokens = 0
                
                # Model pricing (per 1M tokens)
                pricing = {
                    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
                    "gpt-4": {"input": 30.0, "output": 60.0},
                    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
                }
                
                if "data" in data:
                    for item in data["data"]:
                        context_tokens = item.get("n_context_tokens_total", 0)
                        generated_tokens = item.get("n_generated_tokens_total", 0)
                        model = item.get("snapshot_id", "")
                        
                        # Get pricing
                        model_pricing = pricing.get(model, pricing["gpt-4o-mini-2024-07-18"])
                        
                        # Calculate cost
                        input_cost = (context_tokens / 1_000_000) * model_pricing["input"]
                        output_cost = (generated_tokens / 1_000_000) * model_pricing["output"]
                        
                        total_cost += input_cost + output_cost
                        total_tokens += context_tokens + generated_tokens
                
                # Cache today's data
                self.cache_db.set_openai_daily_usage(today, total_tokens, total_cost, data)
                        
                return total_cost, total_tokens
            elif response.status_code == 429:
                logger.warning("OpenAI API rate limited")
                return -429, -429  # Special code for rate limit
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                return -1, -1  # Signal error with negative values
                
        except Exception as e:
            logger.error(f"Error fetching OpenAI data: {e}")
            return -1, -1  # Signal error with negative values
            
    def fetch_gemini_data(self) -> float:
        """Fetch Gemini usage data using Cloud Monitoring and Billing APIs"""
        try:
            # Check if we have Google Cloud credentials
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                logger.info("GOOGLE_CLOUD_PROJECT not set")
                return -1
                
            # Import Google Cloud libraries
            try:
                from google.cloud import monitoring_v3
                from google.cloud import billing_v1
                from google.oauth2 import service_account
                import google.auth
            except ImportError:
                logger.error("Google Cloud packages not installed. Run: pip install -r requirements.txt")
                return -1
            
            # Try to get credentials
            try:
                # First try explicit service account
                service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if service_account_path and os.path.exists(service_account_path):
                    credentials = service_account.Credentials.from_service_account_file(
                        service_account_path
                    )
                else:
                    # Fall back to Application Default Credentials
                    credentials, _ = google.auth.default()
            except Exception as e:
                logger.error(f"Google Cloud auth failed: {e}")
                return -1
            
            # Get today's costs from Cloud Billing
            try:
                billing_client = billing_v1.CloudBillingClient(credentials=credentials)
                
                # Get billing account
                billing_account_name = None
                for account in billing_client.list_billing_accounts():
                    if account.open:
                        billing_account_name = account.name
                        break
                
                if not billing_account_name:
                    logger.error("No open billing account found")
                    return 0.0
                
                # Note: Cloud Billing API doesn't provide real-time usage data
                # It's typically delayed by 24-48 hours
                # For real-time, we'd need to estimate based on request counts
                
                # For now, use Cloud Monitoring to count requests
                monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
                
                # Query for Gemini API requests in the last 24 hours
                project_name = f"projects/{project_id}"
                interval = monitoring_v3.TimeInterval(
                    {
                        "end_time": {"seconds": int(datetime.now().timestamp())},
                        "start_time": {"seconds": int((datetime.now() - timedelta(hours=24)).timestamp())},
                    }
                )
                
                # Count API requests - fix filter syntax
                results = monitoring_client.list_time_series(
                    request={
                        "name": project_name,
                        "filter": 'metric.type="serviceruntime.googleapis.com/api/request_count" '
                                 'AND resource.type="api" '
                                 'AND metadata.user_labels."service"="generativelanguage.googleapis.com"',
                        "interval": interval,
                    }
                )
                
                total_requests = 0
                for result in results:
                    for point in result.points:
                        total_requests += point.value.int64_value
                
                # Estimate cost based on requests
                # Gemini pricing varies by model, but rough estimate:
                # Pro: $0.0025 per 1K chars input, $0.01 per 1K chars output
                # Assuming average request has ~1K input, 2K output
                estimated_cost_per_request = 0.0025 + (0.01 * 2)
                estimated_daily_cost = total_requests * estimated_cost_per_request
                
                logger.info(f"Gemini: {total_requests} requests, estimated ${estimated_daily_cost:.2f}")
                return estimated_daily_cost
                
            except Exception as e:
                logger.error(f"Error querying Google Cloud APIs: {e}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching Gemini data: {e}")
            return -1
            
    def fetch_openrouter_data(self) -> dict:
        """Fetch OpenRouter usage data"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openrouter']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://llm-cost-monitor.app",
                "X-Title": "LLM Cost Monitor"
            }
            
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    api_data = data["data"]
                    return {
                        "usage": api_data.get("usage", 0.0),
                        "limit": api_data.get("limit"),
                        "limit_remaining": api_data.get("limit_remaining"),
                        "is_free_tier": api_data.get("is_free_tier", False),
                        "rate_limit": api_data.get("rate_limit", {}),
                        "label": api_data.get("label", "")
                    }
                    
            return {"usage": 0.0, "limit": None, "is_free_tier": False}
            
        except Exception as e:
            logger.error(f"Error fetching OpenRouter data: {e}")
            return {"usage": 0.0, "limit": None, "is_free_tier": False}
            
    def fetch_api_providers(self):
        """Fetch data from API-based providers only"""
        try:
            daily_usage_total = sum(self.cached_provider_data.get(p, {}).get("cost", 0) 
                                  for p in ["openai", "openrouter", "gemini"])
            
            # OpenAI
            if self.api_keys["openai"]:
                cost, tokens = self.fetch_openai_data()
                if cost == -429:  # Rate limited
                    cached = self.cached_provider_data.get("openai", {"cost": 0.0, "tokens": None})
                    self.provider_cards["openai"].update_display(
                        cached["cost"], cached["tokens"], 
                        "Waiting for API reset"
                    )
                elif cost >= 0:
                    self.cached_provider_data["openai"] = {"cost": cost, "tokens": tokens}
                    self.provider_cards["openai"].update_display(cost, tokens, "Active" if cost > 0 else "No usage today")
                    
                    # Update weekly data if needed
                    if self.openai_weekly_data:
                        self.provider_cards["openai"].update_weekly_data(self.openai_weekly_data)
                else:
                    cached = self.cached_provider_data.get("openai", {"cost": 0.0, "tokens": None})
                    self.provider_cards["openai"].update_display(
                        cached["cost"], cached["tokens"], 
                        "API error"
                    )
            
            # OpenRouter
            if self.api_keys["openrouter"]:
                openrouter_data = self.fetch_openrouter_data()
                cost = openrouter_data.get("usage", 0.0)
                
                # Build status string
                status = "Active" if cost > 0 else "No usage"
                self.provider_cards["openrouter"].update_display(cost, None, status)
                
                # Update detailed info
                if hasattr(self.provider_cards["openrouter"], "update_detailed_info"):
                    self.provider_cards["openrouter"].update_detailed_info(openrouter_data)
            
            # Gemini
            if self.api_keys["gemini"]:
                cost = self.fetch_gemini_data()
                self.provider_cards["gemini"].update_display(cost, None, "Active" if cost > 0 else "No usage")
                if cost >= 0:
                    self.cached_provider_data["gemini"] = {"cost": cost, "tokens": None}
                
            # Update totals
            self.update_totals_display()
            
        except Exception as e:
            logger.error(f"Error in fetch_api_providers: {e}")
            
    def on_provider_clicked(self, provider_name: str):
        """Handle provider card click"""
        logger.info(f"Provider clicked: {provider_name}")
        # TODO: Show detailed view
            
    def update_claude_only(self):
        """Update only Claude Code data"""
        try:
            # This will either return cached data or trigger a background update
            claude_data = self.fetch_claude_code_cached()
            
            # The actual UI update will happen in on_claude_data_ready when background fetch completes
            # But we can still update with cached data if available
            if claude_data['tokens'] > 0 and not self.claude_fetch_in_progress:
                session_start = claude_data.get('session_start')
                rate_history = claude_data.get('rate_history', [])
                
                self.provider_cards["anthropic"].update_display(
                    claude_data['daily'], 
                    claude_data['session'], 
                    claude_data['tokens'],
                    claude_data['session'] > 0,
                    session_start,
                    rate_history
                )
                # Update totals
                self.update_totals_display()
            
        except Exception as e:
            logger.error(f"Error updating Claude: {e}")
            
    def update_totals_display(self):
        """Update the daily and monthly totals display"""
        # Calculate daily total from cached data
        daily_total = sum(self.cached_provider_data.get(p, {}).get("cost", 0) 
                         for p in ["openai", "openrouter", "gemini"])
        
        # Get subscription total
        subscription_total = self.get_claude_subscription_cost()
        
        # Update labels
        self.daily_total_label.setText(f"Daily: ${daily_total:.4f}")
        self.monthly_total_label.setText(f"Subscriptions: ${subscription_total}/mo")
        self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
    def closeEvent(self, event):
        """Handle window close"""
        if self.update_timer:
            self.update_timer.stop()
        if self.claude_update_timer:
            self.claude_update_timer.stop()
        # Stop the worker thread
        if hasattr(self, 'claude_worker'):
            self.claude_worker.stop()
        event.accept()


def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("LLM Cost Monitor Lite")
        
        window = LiteWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()