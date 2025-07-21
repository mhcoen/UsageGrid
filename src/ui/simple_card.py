"""
Simple provider card for standard API providers
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .base_card import BaseProviderCard


class SimpleCard(BaseProviderCard):
    """Simple card for providers that show cost and tokens/requests"""
    
    def __init__(self, provider_name: str, display_name: str, color: str, 
                 metric_name: str = "Tokens", show_estimated: bool = False,
                 size: tuple = (220, 210)):
        self.metric_name = metric_name
        self.show_estimated = show_estimated
        super().__init__(provider_name, display_name, color, size)
        
    def setup_content(self):
        """Add cost and metric labels"""
        # Cost display
        self.cost_label = QLabel("$0.0000")
        if self.show_estimated:
            self.cost_label.setTextFormat(Qt.TextFormat.RichText)
        font = QFont()
        font.setPointSize(self.base_font_sizes['primary'])
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; font-weight: bold;")
        self.layout.addWidget(self.cost_label)
        
        # Metric display (tokens/requests)
        self.metric_label = QLabel(f"{self.metric_name}: -")
        if self.show_estimated and self.metric_name == "Requests":
            self.metric_label.setTextFormat(Qt.TextFormat.RichText)
        self.metric_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['secondary']}px;")
        self.layout.addWidget(self.metric_label)
        
    def update_display(self, data: Dict[str, Any]):
        """Update the card with new data"""
        cost = data.get('cost', 0.0)
        metric_value = data.get('tokens', data.get('requests', None))
        status = data.get('status', 'Active')
        status_type = data.get('status_type', 'normal')
        
        # Update cost
        if self.show_estimated:
            self.cost_label.setText(
                f'${cost:.4f} <span style="font-size: {self.base_font_sizes["small"]}px; '
                f'color: #888; font-weight: normal;">(Estimated)</span>'
            )
        else:
            self.cost_label.setText(f"${cost:.4f}")
            
        # Update metric
        if metric_value is not None:
            if self.show_estimated and self.metric_name == "Requests":
                self.metric_label.setText(
                    f'{self.metric_name}: {metric_value:,} <span style="font-size: '
                    f'{self.base_font_sizes["small"]}px; color: #888;">(Exact)</span>'
                )
            else:
                self.metric_label.setText(f"{self.metric_name}: {metric_value:,}")
        else:
            self.metric_label.setText(f"{self.metric_name}: -")
            
        # Update status
        self.update_status(status, status_type)
        
    def scale_content_fonts(self, scale: float):
        """Scale the content fonts"""
        # Scale cost label
        font = QFont()
        font.setPointSize(int(self.base_font_sizes['primary'] * scale))
        self.cost_label.setFont(font)
        
        # Scale metric label
        self.metric_label.setStyleSheet(
            f"color: #666; font-size: {int(self.base_font_sizes['secondary'] * scale)}px;"
        )
        
        # If using rich text, update the span sizes
        if self.show_estimated:
            cost_text = self.cost_label.text()
            if "(Estimated)" in cost_text:
                # Extract the cost value
                cost_value = cost_text.split(' <span')[0]
                self.cost_label.setText(
                    f'{cost_value} <span style="font-size: {int(self.base_font_sizes["small"] * scale)}px; '
                    f'color: #888; font-weight: normal;">(Estimated)</span>'
                )
                
            metric_text = self.metric_label.text()
            if "(Exact)" in metric_text:
                # Re-enable rich text if needed
                if self.metric_label.textFormat() != Qt.TextFormat.RichText:
                    self.metric_label.setTextFormat(Qt.TextFormat.RichText)
                # Extract the metric value
                parts = metric_text.split(' <span')
                if len(parts) > 1:
                    metric_value = parts[0]
                    self.metric_label.setText(
                        f'{metric_value} <span style="font-size: '
                        f'{int(self.base_font_sizes["small"] * scale)}px; color: #888;">(Exact)</span>'
                    )