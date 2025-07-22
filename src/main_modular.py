#!/usr/bin/env python3
"""
Modular version using configuration-based layout
"""
import sys
import os
import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
import threading
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.providers.claude_code_reader import ClaudeCodeReader
from src.utils.session_helper import find_session_start
from src.core.cache_db import CacheDB
from src.ui.layout_manager import LayoutManager
from src.ui.theme_manager import ThemeManager
# Card registry removed - cards are created directly in layout_manager

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of Claude reader logs
logging.getLogger('src.providers.claude_code_reader').setLevel(logging.DEBUG)


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
        if self._thread and self._thread.is_alive():
            logger.debug("Claude fetch already in progress, skipping")
            return
            
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
            
            # Get total non-cache tokens from session data
            # This was the working calculation before I started messing with it
            total_tokens = session_data.get('total_tokens', 0)
            
            # Get rate history
            rate_history = self.claude_reader.get_token_rate_history(session_start, interval_minutes=0.5)
            
            result = {
                'daily': daily_data['total_cost'],
                'session': session_data['total_cost'],
                'tokens': total_tokens,
                'session_start': session_start,
                'rate_history': rate_history,
                'model_breakdown': session_data.get('model_breakdown', {}),
                'success': True
            }
            
            self.data_ready.emit(result)
            
        except Exception as e:
            logger.error(f"Error in background Claude fetch: {e}")
            self.data_ready.emit({
                'daily': 0.0,
                'session': 0.0,
                'tokens': 0,
                'success': False,
                'error': str(e)
            })
            
    def stop(self):
        """Stop the worker thread"""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=1.0)


class ModularMainWindow(QMainWindow):
    """Main window using modular card architecture"""
    
    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.api_keys = self._load_api_keys()
        self.font_scale = 1.0
        
        # Initialize components
        self.cache_db = CacheDB()
        self.claude_reader = ClaudeCodeReader()
        self.claude_worker = ClaudeDataWorker(self.claude_reader)
        self.claude_worker.data_ready.connect(self.on_claude_data_ready)
        
        # Theme manager
        themes = self.config.get('themes', {})
        default_theme = self.config.get('default_theme', 'light')
        self.theme_manager = ThemeManager(themes, default_theme)
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Layout manager
        self.layout_manager = LayoutManager(self.config.get('layout', {}))
        
        # Cache for provider data
        self.cached_provider_data = {}
        self.cached_claude_data = {}
        self.last_claude_update = None
        self.claude_fetch_in_progress = False
        
        # Theme selector state
        self.theme_selector_active = False
        self.original_gemini_card = None
        
        self.setup_ui()
        self.setup_timers()
        
        # Initial theme
        self.apply_theme()
        
        # Initial fetch
        logger.info("Starting initial data fetch")
        QTimer.singleShot(100, self.fetch_all_data)
        
    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        self.config_path = Path(__file__).parent.parent / "config.json"
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    def _save_config(self):
        """Save configuration to config.json"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        keys = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "anthropic": "",  # Claude Code doesn't use API key
            "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
            "gemini": os.getenv("GOOGLE_CLOUD_PROJECT", "")
        }
        # Log which keys are present (without revealing the actual keys)
        for provider, key in keys.items():
            if key:
                logger.info(f"API key found for {provider}")
            else:
                logger.info(f"No API key for {provider}")
        return keys
        
    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("UsageGrid")
        # Calculate exact window size: 2 columns of 220px + 1px gap + 2px margins = 443px width
        # But we need extra width for header/info indents: 443 + 10 = 453px
        # Height: header(~25) + info(~20) + 2 rows(420) + gap(2) + spacing(1) + margins(2) ≈ 470px
        self.setFixedSize(453, 470)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)  # 1px margins on all sides
        layout.setSpacing(1)  # Reduced vertical spacing from 3 to 1
        
        # Header with daily and subscription totals
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 5, 0)  # Add 5px indent on both sides
        
        self.daily_total_label = QLabel("Daily: $0.00")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.daily_total_label.setFont(font)
        header_layout.addWidget(self.daily_total_label)
        
        header_layout.addStretch()
        
        self.monthly_total_label = QLabel("Subscriptions: $0/mo")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.monthly_total_label.setFont(font)
        header_layout.addWidget(self.monthly_total_label)
        
        layout.addLayout(header_layout)
        
        # Info bar
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(5, 0, 5, 0)  # Same 5px indent as header
        
        self.info_label = QLabel("Fetching real API data...")
        self.info_label.setStyleSheet("color: gray;")
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        self.last_update_label = QLabel("Last update: -")
        self.last_update_label.setStyleSheet("color: gray;")
        info_layout.addWidget(self.last_update_label)
        
        layout.addLayout(info_layout)
        
        # Cards grid using layout manager
        self.cards_layout = self.layout_manager.create_layout(central_widget)
        layout.addLayout(self.cards_layout)
        
        # Connect card clicks
        for card in self.layout_manager.get_all_cards().values():
            card.clicked.connect(self.on_provider_clicked)
        
        central_widget.setLayout(layout)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Setup menu bar
        self.setup_menu()
        
    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Theme submenu
        theme_menu = view_menu.addMenu('Theme')
        for theme_name in self.theme_manager.get_available_themes():
            action = QAction(theme_name.capitalize(), self)
            action.triggered.connect(lambda checked, t=theme_name: self.theme_manager.set_theme(t))
            theme_menu.addAction(action)
            
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Font scaling
        increase_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        increase_shortcut.activated.connect(lambda: self.scale_fonts(1.1))
        
        increase_alt = QShortcut(QKeySequence("Ctrl+="), self)
        increase_alt.activated.connect(lambda: self.scale_fonts(1.1))
        
        decrease_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        decrease_shortcut.activated.connect(lambda: self.scale_fonts(0.9))
        
        reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        reset_shortcut.activated.connect(lambda: self.reset_fonts())
        
        # Theme switching
        theme_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        theme_shortcut.activated.connect(self.toggle_theme)
        
        # Theme selector
        theme_selector_shortcut = QShortcut(QKeySequence("T"), self)
        theme_selector_shortcut.activated.connect(self.show_theme_selector)
        
    def setup_timers(self):
        """Setup update timers"""
        # API providers update every 5 minutes
        self.api_timer = QTimer()
        self.api_timer.timeout.connect(self.fetch_api_providers)
        self.api_timer.start(300000)  # 5 minutes
        
        # Claude Code update every 30 seconds
        self.claude_timer = QTimer()
        self.claude_timer.timeout.connect(self.update_claude_only)
        self.claude_timer.start(30000)  # 30 seconds
        
        # Cache cleanup - every 30 minutes
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_cache)
        self.cleanup_timer.start(1800000)  # 30 minutes
        
    def scale_fonts(self, factor):
        """Scale all fonts by factor"""
        self.font_scale *= factor
        self.update_all_fonts()
        
    def reset_fonts(self):
        """Reset fonts to default size"""
        self.font_scale = 1.0
        self.update_all_fonts()
        
    def update_all_fonts(self):
        """Update all fonts in the UI"""
        # Update header fonts
        font = QFont()
        font.setPointSize(int(18 * self.font_scale))
        font.setBold(True)
        self.daily_total_label.setFont(font)
        self.monthly_total_label.setFont(font)
        
        # Update all cards
        for card in self.layout_manager.get_all_cards().values():
            card.scale_fonts(self.font_scale)
            
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current = self.theme_manager.current_theme
        themes = self.theme_manager.get_available_themes()
        current_idx = themes.index(current)
        next_idx = (current_idx + 1) % len(themes)
        self.theme_manager.set_theme(themes[next_idx])
        
    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self.apply_theme()
        
    def apply_theme(self):
        """Apply current theme to the application"""
        # Apply to main window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme_manager.get_color('background')};
            }}
            QLabel {{
                color: {self.theme_manager.get_color('text_primary')};
            }}
        """)
        
        # Update card styles
        is_dark = self.theme_manager.current_theme in ['dark', 'midnight', 'solarized_dark', 'nord', 'dracula', 'material_dark', 'monokai', 'github_dark']
        for provider, card in self.layout_manager.get_all_cards().items():
            style = self.theme_manager.get_card_style(card.color, card.provider_name)
            card.setStyleSheet(style)
            
            # Update theme-specific colors
            if hasattr(card, 'update_theme_colors'):
                card.update_theme_colors(is_dark)
            
    def fetch_all_data(self):
        """Initial fetch of data from all providers"""
        # Fetch API providers
        self.fetch_api_providers()
        # Fetch Claude Code data
        self.update_claude_only()
        
    def fetch_api_providers(self):
        """Fetch data from API-based providers"""
        daily_usage_total = 0.0
        
        # OpenAI
        if self.api_keys.get("openai"):
            cost, tokens, weekly_data = self.fetch_openai_data()
            if cost >= 0:
                data = {
                    'cost': cost,
                    'tokens': tokens,
                    'weekly_data': weekly_data,
                    'status': 'Active'
                }
                self.layout_manager.update_card_data('openai', data)
                daily_usage_total += cost
            elif cost == -429:
                self.layout_manager.update_card_data('openai', {
                    'cost': self.cached_provider_data.get('openai', {}).get('cost', 0.0),
                    'status': 'Waiting for API reset'
                })
                
        # OpenRouter
        if self.api_keys.get("openrouter"):
            openrouter_data = self.fetch_openrouter_data()
            cost = openrouter_data.get('usage', 0.0)
            data = {
                'cost': cost,
                'detailed_info': openrouter_data,
                'status': 'Active'
            }
            self.layout_manager.update_card_data('openrouter', data)
            daily_usage_total += cost
            
        # Gemini
        gemini_card = self.layout_manager.get_card('gemini')
        if gemini_card and hasattr(gemini_card, 'fetch_data'):
            data = gemini_card.fetch_data()
            self.layout_manager.update_card_data('gemini', data)
            daily_usage_total += data.get('cost', 0.0)
            
        # GitHub (not part of daily usage total - it's not an LLM cost)
        github_card = self.layout_manager.get_card('github')
        if github_card and hasattr(github_card, 'fetch_data'):
            data = github_card.fetch_data()
            self.layout_manager.update_card_data('github', data)
                
        # Update totals
        self.update_totals_display(daily_usage_total)
        
    def fetch_openai_data(self) -> tuple[float, int, dict]:
        """Fetch OpenAI usage data"""
        logger.debug("Fetching OpenAI data")
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "OpenAI-Beta": "usage=1"
            }
            
            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Check cache first
            cached = self.cache_db.get_openai_daily_usage(today)
            if cached:
                total_cost = cached['cost']
                total_tokens = cached['tokens']
            else:
                # Fetch from API
                response = requests.get(
                    f"https://api.openai.com/v1/usage?date={today}",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Calculate costs
                    total_cost = 0.0
                    total_tokens = 0
                    
                    # OpenAI pricing
                    pricing = {
                        "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
                        "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
                        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
                    }
                    
                    if "data" in data:
                        for item in data["data"]:
                            context_tokens = item.get("n_context_tokens_total", 0)
                            generated_tokens = item.get("n_generated_tokens_total", 0)
                            model = item.get("snapshot_id", "")
                            
                            model_pricing = pricing.get(model, pricing["gpt-4o-mini-2024-07-18"])
                            
                            input_cost = (context_tokens / 1_000_000) * model_pricing["input"]
                            output_cost = (generated_tokens / 1_000_000) * model_pricing["output"]
                            
                            total_cost += input_cost + output_cost
                            total_tokens += context_tokens + generated_tokens
                    
                    # Cache today's data
                    self.cache_db.set_openai_daily_usage(today, total_tokens, total_cost, data)
                elif response.status_code == 429:
                    return -429, -429, {}
                else:
                    return -1, -1, {}
                    
            # Get weekly data
            weekly_data = {}
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                cached_day = self.cache_db.get_openai_daily_usage(date)
                if cached_day:
                    weekly_data[date] = {
                        'cost': cached_day['cost'],
                        'tokens': cached_day['tokens']
                    }
                    
            logger.debug(f"OpenAI API returned: cost=${total_cost:.4f}, tokens={total_tokens}")
            return total_cost, total_tokens, weekly_data
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI data: {e}")
            return -1, -1, {}
            
    def fetch_openrouter_data(self) -> dict:
        """Fetch OpenRouter usage data"""
        logger.debug("Fetching OpenRouter data")
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openrouter']}",
                "Content-Type": "application/json"
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
            
            
    def update_claude_only(self):
        """Update only Claude Code data"""
        logger.debug("Updating Claude Code data")
        try:
            claude_data = self.fetch_claude_code_cached()
            
            if claude_data['tokens'] > 0 and not self.claude_fetch_in_progress:
                data = {
                    'daily_cost': claude_data['daily'],
                    'session_cost': claude_data['session'],
                    'tokens': claude_data['tokens'],
                    'is_active': claude_data['tokens'] > 0,
                    'session_start': claude_data.get('session_start'),
                    'initial_rate_data': claude_data.get('rate_history', []),
                    'model_breakdown': claude_data.get('model_breakdown', {})
                }
                self.layout_manager.update_card_data('anthropic', data)
                
        except Exception as e:
            logger.error(f"Error updating Claude data: {e}")
            
    def fetch_claude_code_cached(self) -> dict:
        """Fetch Claude Code data with caching"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Check if we need to update
        if self.last_claude_update:
            time_since_update = (now - self.last_claude_update).total_seconds()
            if time_since_update < 25 and self.cached_claude_data:
                return self.cached_claude_data
                
        # Find current session from actual data
        session_start = find_session_start(now)
        
        # Start background fetch if not already running
        if not self.claude_fetch_in_progress:
            self.claude_fetch_in_progress = True
            self.claude_worker.fetch_data_async(session_start, now)
            
        # Return cached data while waiting
        return self.cached_claude_data if self.cached_claude_data else {
            'daily': 0.0,
            'session': 0.0,
            'tokens': 0,
            'session_start': session_start
        }
        
    def on_claude_data_ready(self, data: dict):
        """Handle Claude data from background thread"""
        self.claude_fetch_in_progress = False
        
        if data['success']:
            self.cached_claude_data = data
            self.last_claude_update = datetime.now(timezone.utc).replace(tzinfo=None)
            logger.debug(f"Claude data received: tokens={data.get('tokens', 0)}, session_cost=${data.get('session', 0):.4f}")
            
            # Update the Claude card
            card_data = {
                'daily_cost': data['daily'],
                'session_cost': data['session'],
                'tokens': data['tokens'],
                'is_active': data['tokens'] > 0,
                'session_start': data.get('session_start'),
                'initial_rate_data': data.get('rate_history', []),
                'model_breakdown': data.get('model_breakdown', {})
            }
            self.layout_manager.update_card_data('anthropic', card_data)
            
            # Log update
            session_start = data.get('session_start')
            if session_start:
                hours_ago = (datetime.now(timezone.utc).replace(tzinfo=None) - session_start).total_seconds() / 3600
                logger.info(f"Claude Code - Session started {hours_ago:.1f}h ago, "
                          f"Daily: ${data['daily']:.2f}, Session: ${data['session']:.2f}, "
                          f"Tokens: {data['tokens']:,}")
                          
            self.info_label.setText("Claude data updated")
            
    def get_claude_subscription_cost(self) -> float:
        """Get Claude subscription monthly cost"""
        claude_config = self.config.get("claude_code", {})
        plan = claude_config.get("subscription_plan", "max20")
        plans = claude_config.get("plans", {})
        plan_info = plans.get(plan, {"monthly_cost": 200})
        return plan_info.get("monthly_cost", 200)
        
    def update_totals_display(self, daily_usage: float = None):
        """Update the totals display"""
        if daily_usage is None:
            daily_usage = sum(self.cached_provider_data.get(p, {}).get("cost", 0) 
                            for p in ["openai", "openrouter", "gemini"])
                            
        subscription_total = self.get_claude_subscription_cost()
        
        self.daily_total_label.setText(f"Daily: ${daily_usage:.4f}")
        self.monthly_total_label.setText(f"Subscriptions: ${subscription_total}/mo")
        self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.info_label.setText("Data updated successfully")
        
    def on_provider_clicked(self, provider_name: str):
        """Handle provider card click"""
        # Close theme selector if clicking outside
        if self.theme_selector_active and provider_name != "theme_selector":
            self.hide_theme_selector()
        else:
            logger.info(f"Provider clicked: {provider_name}")
            # TODO: Show detailed view
        
    def update_single_card(self, provider: str, card):
        """Update a single card"""
        logger.debug(f"Updating card: {provider}")
        try:
            # If the card has its own fetch_data method, use it
            has_custom_fetch = hasattr(card, 'fetch_data') and callable(card.fetch_data)
            if has_custom_fetch:
                logger.debug(f"{provider} has fetch_data method")
                data = card.fetch_data()
                if data is not None:
                    logger.debug(f"{provider} fetch_data returned data")
                    self.layout_manager.update_card_data(provider, data)
                    return  # Exit early if card handled its own data
                else:
                    logger.debug(f"{provider} fetch_data returned None, using main window fetch")
                    
            # Use the main window's fetch methods
            if provider == 'openai' and self.api_keys.get('openai'):
                logger.debug(f"Using main window fetch for OpenAI")
                cost, tokens, weekly = self.fetch_openai_data()
                if cost == -429:
                    data = {
                        'cost': 0.0,
                        'tokens': 0,
                        'status': 'Waiting for API reset',
                        'weekly_data': {}
                    }
                elif cost >= 0:
                    data = {
                        'cost': cost,
                        'tokens': tokens,
                        'status': 'Active' if cost > 0 else 'No usage today',
                        'weekly_data': weekly
                    }
                else:
                    data = {
                        'cost': 0.0,
                        'tokens': 0,
                        'status': 'Error',
                        'weekly_data': {}
                    }
                logger.debug(f"Updating OpenAI card with data: {data}")
                self.layout_manager.update_card_data('openai', data)
            elif provider == 'anthropic':
                self.update_claude_only()
            elif provider == 'openrouter' and self.api_keys.get('openrouter'):
                openrouter_data = self.fetch_openrouter_data()
                data = {
                    'cost': openrouter_data.get('usage', 0.0),
                    'detailed_info': openrouter_data,
                    'status': 'Active'
                }
                self.layout_manager.update_card_data('openrouter', data)
            else:
                logger.debug(f"No update handler for {provider}")
            # Let other cards handle their own updates through fetch_data
        except Exception as e:
            logger.error(f"Error updating {provider}: {e}", exc_info=True)
    
    def cleanup_cache(self):
        """Periodic cleanup of caches"""
        try:
            self.claude_reader.clear_old_cache()
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
        
    def show_theme_selector(self):
        """Show theme selector in place of Gemini card"""
        if self.theme_selector_active:
            return
            
        from src.ui.cards.theme_selector_card import ThemeSelectorCard
        
        # Store original Gemini card
        self.original_gemini_card = self.layout_manager.get_card('gemini')
        
        # Create theme selector
        theme_selector = ThemeSelectorCard(self.config.get('themes', {}), self.theme_manager.current_theme)
        theme_selector.theme_selected.connect(self.on_theme_selected)
        theme_selector.close_requested.connect(self.hide_theme_selector)
        theme_selector.scale_fonts(self.font_scale)
        
        # Replace Gemini card in the layout
        if self.original_gemini_card:
            # Find the stack containing Gemini
            for i in range(self.cards_layout.count()):
                item = self.cards_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        stack_layout = widget.layout() if callable(widget.layout) else widget.layout
                        if stack_layout:
                            # Find Gemini in the stack
                            for j in range(stack_layout.count()):
                                stack_item = stack_layout.itemAt(j)
                                if stack_item and stack_item.widget() == self.original_gemini_card:
                                    # Replace with theme selector
                                    self.original_gemini_card.hide()
                                    stack_layout.insertWidget(j, theme_selector)
                                    theme_selector.show()
                                    theme_selector.theme_list.setFocus()
                                    self.theme_selector_active = True
                                    self.theme_selector_card = theme_selector
                                    return
                                    
    def on_theme_selected(self, theme_name: str):
        """Handle theme selection and save to config"""
        if self.theme_manager.set_theme(theme_name):
            # Update config with new theme
            self.config['default_theme'] = theme_name
            self._save_config()
            
    def hide_theme_selector(self):
        """Hide theme selector and restore Gemini card"""
        if not self.theme_selector_active:
            return
            
        # Find and remove theme selector
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    stack_layout = widget.layout() if callable(widget.layout) else widget.layout
                    if stack_layout:
                        for j in range(stack_layout.count()):
                            stack_item = stack_layout.itemAt(j)
                            if stack_item and hasattr(self, 'theme_selector_card') and stack_item.widget() == self.theme_selector_card:
                                # Remove theme selector
                                self.theme_selector_card.hide()
                                stack_layout.removeWidget(self.theme_selector_card)
                                self.theme_selector_card.deleteLater()
                                
                                # Restore Gemini card
                                if self.original_gemini_card:
                                    stack_layout.insertWidget(j, self.original_gemini_card)
                                    self.original_gemini_card.show()
                                
                                self.theme_selector_active = False
                                return
    
    def closeEvent(self, event):
        """Handle window close"""
        self.claude_worker.stop()
        self.api_timer.stop()
        self.claude_timer.stop()
        self.cleanup_timer.stop()
        event.accept()


def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("UsageGrid")
        
        window = ModularMainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()