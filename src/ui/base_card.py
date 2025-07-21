"""
Base card class for modular provider cards
"""
from abc import abstractmethod
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class BaseProviderCard(QFrame):
    """Abstract base class for all provider cards"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str, size: Tuple[int, int] = (220, 210)):
        super().__init__()
        self.provider_name = provider_name
        self.display_name = display_name
        self.color = color
        self.width, self.height = size
        self.base_font_sizes = {
            'title': 16,
            'primary': 24,
            'secondary': 13,
            'small': 11
        }
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the basic card UI"""
        self.setFixedSize(self.width, self.height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(2)
        
        # Add title
        self.title_label = QLabel(self.display_name)
        font = QFont()
        font.setPointSize(self.base_font_sizes['title'])
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #333;")
        self.layout.addWidget(self.title_label)
        
        # Let subclasses add their content
        self.setup_content()
        
        # Add stretch to push status to bottom
        self.layout.addStretch()
        
        # Add status label at bottom
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet(f"color: gray; font-size: {self.base_font_sizes['secondary']}px;")
        self.layout.addWidget(self.status_label)
        
        self.setLayout(self.layout)
        
    @abstractmethod
    def setup_content(self):
        """Subclasses must implement this to add their specific content"""
        pass
        
    @abstractmethod
    def update_display(self, data: Dict[str, Any]):
        """Update the card display with new data"""
        pass
        
    def update_status(self, status: str, status_type: str = "normal"):
        """Update the status label"""
        self.status_label.setText(status)
        
        # Update status color based on type
        if status_type == "active":
            self.status_label.setStyleSheet(f"color: #28a745; font-size: {self.base_font_sizes['secondary']}px;")
        elif status_type == "warning":
            self.status_label.setStyleSheet(f"color: #ff6b35; font-size: {self.base_font_sizes['secondary']}px; font-weight: bold;")
        elif status_type == "error":
            self.status_label.setStyleSheet(f"color: #dc3545; font-size: {self.base_font_sizes['secondary']}px;")
        else:
            self.status_label.setStyleSheet(f"color: gray; font-size: {self.base_font_sizes['secondary']}px;")
            
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)
            
    def scale_fonts(self, scale: float):
        """Scale all fonts in the card"""
        # Scale title
        font = QFont()
        font.setPointSize(int(self.base_font_sizes['title'] * scale))
        font.setBold(True)
        self.title_label.setFont(font)
        
        # Scale status (preserve color)
        current_style = self.status_label.styleSheet()
        size = int(self.base_font_sizes['secondary'] * scale)
        if "color: #28a745" in current_style:  # Active
            self.status_label.setStyleSheet(f"color: #28a745; font-size: {size}px;")
        elif "color: #ff6b35" in current_style:  # Warning
            self.status_label.setStyleSheet(f"color: #ff6b35; font-size: {size}px; font-weight: bold;")
        elif "color: #dc3545" in current_style:  # Error
            self.status_label.setStyleSheet(f"color: #dc3545; font-size: {size}px;")
        else:  # Normal
            self.status_label.setStyleSheet(f"color: gray; font-size: {size}px;")
            
        # Let subclasses scale their content
        self.scale_content_fonts(scale)
        
    def scale_content_fonts(self, scale: float):
        """Subclasses can override this to scale their specific content"""
        pass