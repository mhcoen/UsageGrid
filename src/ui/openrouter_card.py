"""
Enhanced OpenRouter card with detailed information display
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Any, Tuple, Optional
from .base_card import BaseProviderCard


class OpenRouterCard(BaseProviderCard):
    """Enhanced OpenRouter provider card with detailed information"""
    
    def __init__(self, size: Tuple[int, int] = (220, 210)):
        self.is_half_height = size[1] < 150
        super().__init__(
            provider_name="openrouter",
            display_name="OpenRouter",
            color="#ee4b2b",
            size=size
        )
        
    def setup_content(self):
        """Add OpenRouter-specific content"""
        # Cost display
        self.cost_label = QLabel("$0.00")
        font = QFont()
        font.setPointSize(self.base_font_sizes['primary'] if not self.is_half_height else self.base_font_sizes['secondary'])
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; font-weight: bold;")
        self.layout.addWidget(self.cost_label)
        
        # Always show additional info, just with smaller font for half-height
        # Limit info
        self.limit_label = QLabel("")
        self.limit_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['small']}px;")
        self.layout.addWidget(self.limit_label)
        
        # Rate limit info
        self.rate_limit_label = QLabel("")
        self.rate_limit_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['small']}px;")
        self.rate_limit_label.setWordWrap(True)
        self.layout.addWidget(self.rate_limit_label)
        
        # Free tier indicator
        self.free_tier_label = QLabel("")
        self.free_tier_label.setStyleSheet(f"color: #28a745; font-size: {self.base_font_sizes['small']}px; font-weight: bold;")
        self.layout.addWidget(self.free_tier_label)
        
    def update_display(self, data: Dict[str, Any]):
        """Update the card display"""
        cost = data.get('cost', 0.0)
        status = data.get('status', 'Active')
        detailed_info = data.get('detailed_info', {})
        
        # Update cost
        self.cost_label.setText(f"${cost:.4f}")
        
        # Update detailed info if available
        if detailed_info:
            self.update_detailed_info(detailed_info)
            
        # Update status
        status_type = "normal"
        if "Active" in status:
            status_type = "active"
        elif "Error" in status:
            status_type = "error"
            
        self.update_status(status, status_type)
            
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
            if hasattr(self, 'limit_label'):
                self.limit_label.hide()
            
        # Update rate limit info
        rate_limit = data.get("rate_limit", {})
        if rate_limit:
            requests = rate_limit.get("requests", "-")
            requests_remaining = rate_limit.get("requests_remaining", "-")
            self.rate_limit_label.setText(f"Rate limit: {requests_remaining}/{requests} requests")
            self.rate_limit_label.show()
        else:
            if hasattr(self, 'rate_limit_label'):
                self.rate_limit_label.hide()
            
        # Update free tier indicator
        if data.get("is_free_tier"):
            self.free_tier_label.setText("✓ Free tier active")
            self.free_tier_label.show()
        else:
            if hasattr(self, 'free_tier_label'):
                self.free_tier_label.hide()
                
    def scale_content_fonts(self, scale: float):
        """Scale OpenRouter-specific fonts"""
        # Scale cost label
        font = QFont()
        font.setPointSize(int(self.base_font_sizes['primary'] * scale))
        self.cost_label.setFont(font)
        
        # Scale other labels if they exist
        if hasattr(self, 'limit_label'):
            self.limit_label.setStyleSheet(f"color: #666; font-size: {int(self.base_font_sizes['small'] * scale)}px;")
        if hasattr(self, 'rate_limit_label'):
            self.rate_limit_label.setStyleSheet(f"color: #666; font-size: {int(self.base_font_sizes['small'] * scale)}px;")
        if hasattr(self, 'free_tier_label'):
            self.free_tier_label.setStyleSheet(f"color: #28a745; font-size: {int(self.base_font_sizes['small'] * scale)}px; font-weight: bold;")