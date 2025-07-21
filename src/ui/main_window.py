"""
Main window for LLM Cost Monitor
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import logging

from src.core.database import Database
from src.core.polling_engine import PollingEngine

logger = logging.getLogger(__name__)


class ProviderCard(QFrame):
    """Widget for displaying provider status"""
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str):
        super().__init__()
        self.provider_name = provider_name
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Provider name
        self.name_label = QLabel(display_name)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Cost display
        self.cost_label = QLabel("$0.00")
        font = QFont()
        font.setPointSize(18)
        self.cost_label.setFont(font)
        layout.addWidget(self.cost_label)
        
        # Status
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        # Trend (placeholder)
        self.trend_label = QLabel("─ 0%")
        layout.addWidget(self.trend_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet(f"""
            ProviderCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
            ProviderCard:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)
            
    def update_data(self, cost: float, status: str = "Active"):
        """Update the displayed data"""
        self.cost_label.setText(f"${cost:.2f}")
        self.status_label.setText(status)
        
        if status == "Active":
            self.status_label.setStyleSheet("color: green;")
        elif status == "Error":
            self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setStyleSheet("color: gray;")


class MainWindow(QMainWindow):
    def __init__(self, database: Database, polling_engine: PollingEngine):
        super().__init__()
        self.db = database
        self.polling_engine = polling_engine
        self.provider_cards = {}
        
        self.setup_ui()
        self.load_providers()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("LLM Cost Monitor")
        self.setMinimumSize(800, 600)
        
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
        font.setPointSize(24)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.total_label = QLabel("Total: $0.00")
        font = QFont()
        font.setPointSize(18)
        self.total_label.setFont(font)
        header_layout.addWidget(self.total_label)
        
        layout.addLayout(header_layout)
        
        # Provider grid
        self.provider_grid = QGridLayout()
        self.provider_grid.setSpacing(15)
        
        # Placeholder for providers
        placeholder = QLabel("No providers configured")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; padding: 50px;")
        self.provider_grid.addWidget(placeholder, 0, 0)
        
        layout.addLayout(self.provider_grid)
        layout.addStretch()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        central_widget.setLayout(layout)
        
    def load_providers(self):
        """Load providers from database"""
        # This will be implemented when we have providers registered
        pass
        
    def add_provider_card(self, provider_name: str, display_name: str, color: str):
        """Add a provider card to the display"""
        card = ProviderCard(provider_name, display_name, color)
        card.clicked.connect(self.on_provider_clicked)
        
        # Add to grid (2 columns)
        row = len(self.provider_cards) // 2
        col = len(self.provider_cards) % 2
        
        # Remove placeholder if this is the first card
        if len(self.provider_cards) == 0:
            item = self.provider_grid.itemAtPosition(0, 0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        self.provider_grid.addWidget(card, row, col)
        self.provider_cards[provider_name] = card
        
    def on_provider_clicked(self, provider_name: str):
        """Handle provider card click"""
        logger.info(f"Provider clicked: {provider_name}")
        # TODO: Show detailed view
        
    def update_display(self):
        """Update the display with latest data"""
        # Get status from polling engine
        statuses = self.polling_engine.get_all_statuses()
        
        total_cost = 0.0
        
        for name, status in statuses.items():
            if name in self.provider_cards and status:
                card = self.provider_cards[name]
                
                if status['last_data']:
                    cost = status['last_data'].total_cost
                    card.update_data(cost, "Active")
                    total_cost += cost
                else:
                    card.update_data(0.0, "Waiting...")
                    
        self.total_label.setText(f"Total: ${total_cost:.2f}")
        
    def closeEvent(self, event):
        """Handle window close"""
        logger.info("Main window closing")
        event.accept()