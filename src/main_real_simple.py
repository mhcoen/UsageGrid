#!/usr/bin/env python3
"""
Simple version with real API data - no complex async
"""
import sys
import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.providers.claude_code_reader import ClaudeCodeReader
from src.providers.claude_code_session import ClaudeCodeSession

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        self.cost_label.setText(f"${cost:.4f}")
        
        if tokens is not None:
            self.token_label.setText(f"Tokens: {tokens:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        self.status_label.setText(status)
        
        # Update status color
        if status == "Active":
            self.status_label.setStyleSheet("color: #28a745;")
        elif "Error" in status:
            self.status_label.setStyleSheet("color: #dc3545;")
        else:
            self.status_label.setStyleSheet("color: gray;")


class RealDataWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.provider_cards = {}
        self.api_keys = {}
        self.update_timer = None
        
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
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("LLM Cost Monitor - Real Data")
        self.setMinimumSize(900, 650)
        
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
        
        self.total_label = QLabel("Total: $0.0000")
        font = QFont()
        font.setPointSize(20)
        self.total_label.setFont(font)
        header_layout.addWidget(self.total_label)
        
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
        providers = [
            ("openai", "OpenAI", "#10a37f"),
            ("anthropic", "Claude Code", "#e16e3d"),
            ("openrouter", "OpenRouter", "#8b5cf6"),
            ("gemini", "Gemini", "#4285f4")
        ]
        
        for i, (name, display_name, color) in enumerate(providers):
            card = SimpleProviderCard(name, display_name, color)
            
            # Add to grid (2 columns)
            row = i // 2
            col = i % 2
            
            self.provider_grid.addWidget(card, row, col)
            self.provider_cards[name] = card
            
    def start_updates(self):
        """Start the update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.fetch_all_data)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial fetch
        self.fetch_all_data()
        
    def fetch_all_data(self):
        """Fetch data from all providers"""
        total_cost = 0.0
        
        # OpenAI
        if self.api_keys["openai"]:
            cost, tokens = self.fetch_openai_data()
            self.provider_cards["openai"].update_display(cost, tokens, "Active" if cost > 0 else "No usage today")
            total_cost += cost
        else:
            self.provider_cards["openai"].update_display(0.0, None, "No API key")
            
        # OpenRouter
        if self.api_keys["openrouter"]:
            cost = self.fetch_openrouter_data()
            self.provider_cards["openrouter"].update_display(cost, None, "Active" if cost > 0 else "No usage")
            total_cost += cost
        else:
            self.provider_cards["openrouter"].update_display(0.0, None, "No API key")
            
        # Claude Code
        cost, tokens = self.fetch_claude_code_data()
        logger.info(f"Claude Code fetch returned: cost=${cost}, tokens={tokens}")
        if cost > 0:
            self.provider_cards["anthropic"].update_display(cost, tokens, "Active Session")
            total_cost += cost
        else:
            self.provider_cards["anthropic"].update_display(0.0, None, "No active session")
            
        # Gemini
        if self.api_keys["gemini"]:
            cost = self.fetch_gemini_data()
            self.provider_cards["gemini"].update_display(cost, None, "Active" if cost > 0 else "No usage")
            total_cost += cost
        else:
            self.provider_cards["gemini"].update_display(0.0, None, "No API key")
            
        # Update total and timestamp
        self.total_label.setText(f"Total: ${total_cost:.4f}")
        self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.statusBar().showMessage("Data updated successfully")
        
    def fetch_openai_data(self) -> tuple[float, int]:
        """Fetch OpenAI usage data"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "Content-Type": "application/json"
            }
            
            # Get today's date
            today = datetime.utcnow().date().isoformat()
            
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
                        
                return total_cost, total_tokens
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                return 0.0, 0
                
        except Exception as e:
            logger.error(f"Error fetching OpenAI data: {e}")
            return 0.0, 0
            
    def fetch_openrouter_data(self) -> float:
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
                    return data["data"].get("usage", 0.0)
                    
            return 0.0
            
        except Exception as e:
            logger.error(f"Error fetching OpenRouter data: {e}")
            return 0.0
            
    def fetch_gemini_data(self) -> float:
        """Fetch Gemini usage data"""
        # Note: Google doesn't provide a usage API for Gemini
        # This is a placeholder for future implementation
        return 0.0
            
    def fetch_claude_code_data(self) -> tuple[float, int]:
        """Fetch Claude Code usage data - active session only"""
        try:
            session = ClaudeCodeSession()
            # Get active session usage (like Claude Monitor)
            session_data = session.get_active_session_usage()
            
            if session_data['is_active']:
                logger.info(f"Claude Code active session: ${session_data['cost']:.4f}, "
                           f"{session_data['tokens']} tokens, {session_data['messages']} messages")
                return session_data['cost'], session_data['tokens']
            else:
                logger.info("No active Claude Code session")
                return 0.0, 0
            
        except Exception as e:
            logger.error(f"Error reading Claude Code data: {e}")
            return 0.0, 0
            
    def closeEvent(self, event):
        """Handle window close"""
        if self.update_timer:
            self.update_timer.stop()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Cost Monitor")
    
    window = RealDataWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()