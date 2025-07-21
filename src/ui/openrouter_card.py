"""
Enhanced OpenRouter card with detailed information display
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Optional


class OpenRouterCard(QFrame):
    """Enhanced OpenRouter provider card with detailed information"""
    clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.provider_name = "openrouter"
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(220, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Provider name
        self.name_label = QLabel("OpenRouter")
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
        
        # Status
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Limit info
        self.limit_label = QLabel("")
        self.limit_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.limit_label)
        
        # Rate limit info
        self.rate_limit_label = QLabel("")
        self.rate_limit_label.setStyleSheet("color: #666; font-size: 11px;")
        self.rate_limit_label.setWordWrap(True)
        layout.addWidget(self.rate_limit_label)
        
        # Free tier indicator
        self.free_tier_label = QLabel("")
        self.free_tier_label.setStyleSheet("color: #28a745; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.free_tier_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            OpenRouterCard {
                background-color: white;
                border: 2px solid #ee4b2b;
                border-radius: 10px;
            }
            OpenRouterCard:hover {
                background-color: #f8f9fa;
            }
        """)
        
    def update_display(self, cost: float, tokens: Optional[int], status: str):
        """Update the basic display"""
        # Always show 4 decimal places for daily cost
        self.cost_label.setText(f"${cost:.4f}")
        self.status_label.setText(status)
        
        # Update status color
        if "Active" in status:
            self.status_label.setStyleSheet("color: #28a745; font-size: 11px;")
        elif "Error" in status:
            self.status_label.setStyleSheet("color: #dc3545; font-size: 11px;")
        else:
            self.status_label.setStyleSheet("color: gray; font-size: 11px;")
            
    def update_detailed_info(self, data: Dict):
        """Update detailed information display"""
        # Update limit info
        if data.get("limit_remaining") is not None and data.get("limit") is not None:
            remaining = data["limit_remaining"]
            total = data["limit"]
            self.limit_label.setText(f"Credits: ${remaining:.2f} / ${total:.2f}")
            self.limit_label.show()
        elif data.get("limit"):
            self.limit_label.setText(f"Usage limit: ${data['limit']:.2f}")
            self.limit_label.show()
        else:
            self.limit_label.hide()
            
        # Update rate limit info
        rate_limit = data.get("rate_limit", {})
        if rate_limit:
            requests = rate_limit.get("requests", "-")
            requests_remaining = rate_limit.get("requests_remaining", "-")
            self.rate_limit_label.setText(f"Rate limit: {requests_remaining}/{requests} requests")
            self.rate_limit_label.show()
        else:
            self.rate_limit_label.hide()
            
        # Update free tier indicator
        if data.get("is_free_tier"):
            self.free_tier_label.setText("✓ Free tier active")
            self.free_tier_label.show()
        else:
            self.free_tier_label.hide()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)