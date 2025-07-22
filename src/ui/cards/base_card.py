"""
Base card class for modular provider cards
"""
from abc import abstractmethod
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QDesktopServices, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import QUrl


class KeyIndicator(QLabel):
    """Small widget to show active key count with colored circle"""
    
    def __init__(self):
        super().__init__()
        self.total_keys = 0
        self.active_keys = 0
        self.setFixedSize(20, 20)
        
    def set_key_status(self, active: int, total: int):
        """Update the key status"""
        self.active_keys = active
        self.total_keys = total
        if total > 1:
            self.setVisible(True)
            self.update()
        else:
            self.setVisible(False)
            
    def paintEvent(self, event):
        """Paint the colored circle with number"""
        if self.total_keys <= 1:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine color based on status
        if self.active_keys == self.total_keys:
            color = QColor("#4CAF50")  # Green
        elif self.active_keys > 1:
            color = QColor("#FF9800")  # Orange
        elif self.active_keys == 1:
            color = QColor("#F44336")  # Red
        else:
            color = QColor("#9E9E9E")  # Gray
            
        # Draw circle
        painter.setPen(QPen(color.darker(120), 1))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(1, 1, 18, 18)
        
        # Draw text
        painter.setPen(QPen(Qt.GlobalColor.white))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.active_keys))


class BaseProviderCard(QFrame):
    """Abstract base class for all provider cards"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str, size: Tuple[int, int] = (220, 210), show_status: bool = True):
        super().__init__()
        self.provider_name = provider_name
        self.display_name = display_name
        self.color = color
        self.width, self.height = size
        self.show_status = show_status
        self.base_font_sizes = {
            'title': 15,
            'primary': 24,
            'secondary': 13,
            'small': 11
        }
        # Billing URL - to be set by subclasses
        self.billing_url = None
        # Update interval in milliseconds - to be set by subclasses
        self.update_interval = 300000  # Default 5 minutes
        # Whether this card should auto-update
        self.auto_update = True
        # Multi-key support
        self.total_keys = 0
        self.active_keys = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the basic card UI"""
        self.setFixedSize(self.width, self.height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(2)
        
        # Add title with horizontal layout for key indicator
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        self.title_label = QLabel(self.display_name)
        font = QFont()
        font.setPointSize(self.base_font_sizes['title'])
        font.setBold(True)
        self.title_label.setFont(font)
        title_layout.addWidget(self.title_label)
        
        # Key indicator widget
        self.key_indicator = KeyIndicator()
        self.key_indicator.setVisible(False)  # Hidden by default
        title_layout.addWidget(self.key_indicator)
        
        title_layout.addStretch()
        self.layout.addLayout(title_layout)
        
        # Let subclasses add their content
        self.setup_content()
        
        # Add stretch to push status to bottom
        self.layout.addStretch()
        
        # Add status label at bottom if enabled
        if self.show_status:
            self.status_label = QLabel("Checking...")
            self.status_label.setStyleSheet(f"color: gray; font-size: {self.base_font_sizes['secondary']}px;")
            self.layout.addWidget(self.status_label)
        else:
            self.status_label = None
        
        self.setLayout(self.layout)
        
    @abstractmethod
    def setup_content(self):
        """Subclasses must implement this to add their specific content"""
        pass
        
    def enable_billing_link(self):
        """Enable clickable title if billing URL is set"""
        if self.billing_url and self.title_label:
            self.title_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.title_label.setToolTip(f"Click to open {self.display_name} billing page")
            self.title_label.setMouseTracking(True)
            self.title_label.installEventFilter(self)
        
    @abstractmethod
    def update_display(self, data: Dict[str, Any]):
        """Update the card display with new data"""
        pass
        
        
    def update_status(self, status: str, status_type: str = "normal"):
        """Update the status label"""
        if not self.status_label:
            return
            
        self.status_label.setText(status)
        
        # Update status color based on type
        if status_type == "active":
            self.status_label.setStyleSheet(f"color: #28a745; font-size: {self.base_font_sizes['secondary']}px;")
        elif status_type == "warning":
            self.status_label.setStyleSheet(f"color: #ff6b35; font-size: {self.base_font_sizes['secondary']}px; font-weight: bold;")
        elif status_type == "error":
            self.status_label.setStyleSheet(f"color: #dc3545; font-size: {self.base_font_sizes['secondary']}px;")
        elif status_type == "italic":
            self.status_label.setStyleSheet(f"color: gray; font-size: {self.base_font_sizes['secondary'] - 2}px; font-style: italic;")
        else:
            self.status_label.setStyleSheet(f"color: gray; font-size: {self.base_font_sizes['secondary']}px;")
            
    def update_key_status(self, active_keys: int, total_keys: int):
        """Update the key indicator"""
        self.key_indicator.set_key_status(active_keys, total_keys)
            
    def eventFilter(self, source, event):
        """Handle events for child widgets"""
        if source == self.title_label and self.billing_url:
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Open billing URL
                    QDesktopServices.openUrl(QUrl(self.billing_url))
                    return True
            elif event.type() == event.Type.Enter:
                # Add underline on hover
                font = self.title_label.font()
                font.setUnderline(True)
                self.title_label.setFont(font)
                return True
            elif event.type() == event.Type.Leave:
                # Remove underline
                font = self.title_label.font()
                font.setUnderline(False)
                self.title_label.setFont(font)
                return True
        return super().eventFilter(source, event)
    
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
        
        # Scale status (preserve color and style)
        if self.status_label:
            current_style = self.status_label.styleSheet()
            size = int(self.base_font_sizes['secondary'] * scale)
            if "color: #28a745" in current_style:  # Active
                self.status_label.setStyleSheet(f"color: #28a745; font-size: {size}px;")
            elif "color: #ff6b35" in current_style:  # Warning
                self.status_label.setStyleSheet(f"color: #ff6b35; font-size: {size}px; font-weight: bold;")
            elif "color: #dc3545" in current_style:  # Error
                self.status_label.setStyleSheet(f"color: #dc3545; font-size: {size}px;")
            elif "font-style: italic" in current_style:  # Italic (1pt smaller)
                self.status_label.setStyleSheet(f"color: gray; font-size: {size - 1}px; font-style: italic;")
            else:  # Normal
                self.status_label.setStyleSheet(f"color: gray; font-size: {size}px;")
            
        # Let subclasses scale their content
        self.scale_content_fonts(scale)
        
    def scale_content_fonts(self, scale: float):
        """Subclasses can override this to scale their specific content"""
        pass
        
    def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data for this provider. Override in subclasses that fetch their own data."""
        return None