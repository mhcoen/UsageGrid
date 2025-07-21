#!/usr/bin/env python3
"""
LLM Cost Monitor - Simplified async version with mock data support
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
import random
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockProviderData:
    """Mock data generator for demonstration"""
    def __init__(self):
        self.base_cost = random.uniform(20.0, 40.0)
        self.base_tokens = random.randint(50000, 80000)
        
    def get_data(self):
        """Get mock data with slight variations"""
        # Add some variation to make it look real
        cost_variation = random.uniform(-2.0, 2.0)
        token_variation = random.randint(-5000, 5000)
        
        return {
            "cost": max(0, self.base_cost + cost_variation),
            "tokens": max(0, self.base_tokens + token_variation),
            "status": "Active"
        }


class ProviderCard(QFrame):
    """Simple provider card widget"""
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str):
        super().__init__()
        self.provider_name = provider_name
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.name_label.setStyleSheet("color: #333; background-color: transparent;")
        layout.addWidget(self.name_label)
        
        # Cost display
        self.cost_label = QLabel("$0.00")
        font = QFont()
        font.setPointSize(20)
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; background-color: transparent; font-weight: bold;")
        layout.addWidget(self.cost_label)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet("color: #666;")
        layout.addWidget(self.token_label)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet(f"""
            ProviderCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
            }}
            ProviderCard:hover {{
                background-color: #f8f9fa;
                border: 3px solid {color};
            }}
        """)
        
    def update_display(self, cost: float, tokens: int, status: str):
        """Update the card display"""
        self.cost_label.setText(f"${cost:.2f}")
        self.token_label.setText(f"Tokens: {tokens:,}")
        self.status_label.setText(status)
        
        # Update status color
        if status == "Active":
            self.status_label.setStyleSheet("color: #28a745;")
        else:
            self.status_label.setStyleSheet("color: gray;")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)


class SimpleLLMMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.provider_cards = {}
        self.mock_data = {}
        self.update_timer = None
        self.setup_ui()
        self.setup_providers()
        self.start_updates()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("LLM Cost Monitor - Demo Mode")
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
        
        # Demo mode indicator
        demo_label = QLabel("(Demo Mode)")
        demo_label.setStyleSheet("color: #ffc107; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(demo_label)
        
        header_layout.addStretch()
        
        self.total_label = QLabel("Total: $0.00")
        font = QFont()
        font.setPointSize(20)
        self.total_label.setFont(font)
        header_layout.addWidget(self.total_label)
        
        layout.addLayout(header_layout)
        
        # Info bar
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Showing mock data for demonstration")
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
        self.statusBar().showMessage("Demo mode - Showing simulated data")
        
        central_widget.setLayout(layout)
        
    def setup_providers(self):
        """Setup provider cards"""
        providers = [
            ("openai", "OpenAI", "#10a37f"),
            ("anthropic", "Anthropic", "#e16e3d"),
            ("openrouter", "OpenRouter", "#8b5cf6"),
            ("huggingface", "HuggingFace", "#ffbe0b")
        ]
        
        for i, (name, display_name, color) in enumerate(providers):
            card = ProviderCard(name, display_name, color)
            card.clicked.connect(self.on_provider_clicked)
            
            # Add to grid (2 columns)
            row = i // 2
            col = i % 2
            
            self.provider_grid.addWidget(card, row, col)
            self.provider_cards[name] = card
            
            # Initialize mock data for all providers for demo
            self.mock_data[name] = MockProviderData()
            
    def start_updates(self):
        """Start the update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
    def update_display(self):
        """Update the display with mock data"""
        total_cost = 0.0
        
        for name, card in self.provider_cards.items():
            if name in self.mock_data:
                # Get mock data
                data = self.mock_data[name].get_data()
                card.update_display(data["cost"], data["tokens"], data["status"])
                total_cost += data["cost"]
            else:
                # Other providers show waiting
                card.update_display(0.0, 0, "No adapter implemented")
                
        self.total_label.setText(f"Total: ${total_cost:.2f}")
        self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
    def on_provider_clicked(self, provider_name: str):
        """Handle provider click"""
        from PyQt6.QtWidgets import QMessageBox
        
        if provider_name in self.mock_data:
            QMessageBox.information(
                self,
                f"{provider_name.title()} Provider",
                f"This is showing mock data for demonstration.\n\n"
                "In a real deployment with valid API keys,\n"
                "this would show actual usage data."
            )
        else:
            QMessageBox.information(
                self,
                f"{provider_name.title()} Provider",
                f"Provider adapter not implemented yet.\n\n"
                "Only OpenAI is currently showing mock data."
            )
            
    def closeEvent(self, event):
        """Handle window close"""
        if self.update_timer:
            self.update_timer.stop()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Cost Monitor Demo")
    
    window = SimpleLLMMonitorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()