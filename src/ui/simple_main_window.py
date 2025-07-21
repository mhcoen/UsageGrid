"""
Simple main window without async complexity
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import logging
import os

logger = logging.getLogger(__name__)


class SimpleProviderCard(QFrame):
    """Simple provider card widget"""
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str):
        super().__init__()
        self.provider_name = provider_name
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(200, 150)
        
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
        self.status_label = QLabel("No API Key" if not os.getenv(f"{provider_name.upper()}_API_KEY") else "Ready")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet(f"""
            SimpleProviderCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
            SimpleProviderCard:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)


class SimpleMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.provider_cards = {}
        self.setup_ui()
        self.add_providers()
        
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
        
        # Info label
        info_label = QLabel("Configure API keys as environment variables to enable providers")
        info_label.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info_label)
        
        # Provider grid
        self.provider_grid = QGridLayout()
        self.provider_grid.setSpacing(15)
        layout.addLayout(self.provider_grid)
        
        layout.addStretch()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        central_widget.setLayout(layout)
        
    def add_providers(self):
        """Add provider cards"""
        providers = [
            ("openai", "OpenAI", "#10a37f"),
            ("anthropic", "Anthropic", "#e16e3d"),
            ("openrouter", "OpenRouter", "#8b5cf6"),
            ("huggingface", "HuggingFace", "#ffbe0b")
        ]
        
        for i, (name, display_name, color) in enumerate(providers):
            card = SimpleProviderCard(name, display_name, color)
            card.clicked.connect(self.on_provider_clicked)
            
            row = i // 2
            col = i % 2
            
            self.provider_grid.addWidget(card, row, col)
            self.provider_cards[name] = card
            
    def on_provider_clicked(self, provider_name: str):
        """Handle provider card click"""
        env_var = f"{provider_name.upper()}_API_KEY"
        if os.getenv(env_var):
            QMessageBox.information(
                self,
                f"{provider_name.title()} Provider",
                f"API key found for {provider_name.title()}.\n\n"
                "Full async polling not implemented in simple mode.\n"
                "Use the async version for real-time updates."
            )
        else:
            QMessageBox.warning(
                self,
                f"{provider_name.title()} Provider",
                f"No API key found for {provider_name.title()}.\n\n"
                f"Set the {env_var} environment variable to enable this provider."
            )
        
    def closeEvent(self, event):
        """Handle window close"""
        logger.info("Main window closing")
        event.accept()