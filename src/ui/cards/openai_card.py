"""
Enhanced OpenAI card with bar chart visualization
"""
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from datetime import datetime
from typing import Dict, Any, Optional
from .base_card import BaseProviderCard


class BarChartWidget(QWidget):
    """Simple bar chart widget for displaying weekly data"""
    
    def __init__(self):
        super().__init__()
        self.data = {}  # {date_str: value}
        self.setMinimumHeight(50)
        self.setMaximumHeight(60)
        
    def set_data(self, data: Dict[str, float]):
        """Set the data to display"""
        self.data = data
        self.update()
        
    def paintEvent(self, event):
        """Paint the bar chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            return
            
        # Sort data by date (earliest to latest)
        sorted_dates = sorted(self.data.keys())[:7]  # Last 7 days
        
        if not sorted_dates:
            return
            
        # Calculate dimensions
        margin = 5
        bar_width = (self.width() - 2 * margin) / len(sorted_dates) - 5
        max_value = max(self.data.values()) if max(self.data.values()) > 0 else 1
        chart_height = self.height() - 2 * margin - 15  # Leave room for labels
        
        # Draw bars
        for i, date_str in enumerate(sorted_dates):
            value = self.data.get(date_str, 0)
            
            # Calculate bar position and height
            x = int(margin + i * (bar_width + 5))
            bar_height = int((value / max_value) * chart_height) if max_value > 0 else 0
            y = int(self.height() - margin - 15 - bar_height)
            bar_width_int = int(bar_width)
            
            # Draw bar
            if value > 0:
                painter.fillRect(x, y, bar_width_int, bar_height, QBrush(QColor(16, 163, 127)))
            
            # Draw date label
            date_obj = datetime.fromisoformat(date_str)
            label = date_obj.strftime("%m/%d")
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Arial", 8))
            label_rect = painter.boundingRect(x, self.height() - 15, bar_width_int, 15, 
                                            Qt.AlignmentFlag.AlignCenter, label)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
            
            # Draw value on top of bar if it's tall enough
            if bar_height > 20 and value > 0:
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                value_text = f"${value:.2f}" if value < 100 else f"${int(value)}"
                painter.drawText(x, y + 2, bar_width_int, 20, 
                               Qt.AlignmentFlag.AlignCenter, value_text)


class OpenAICard(BaseProviderCard):
    """Enhanced OpenAI provider card with bar chart"""
    
    def __init__(self):
        self.weekly_data = {}
        super().__init__(
            provider_name="openai",
            display_name="OpenAI",
            color="#10a37f"
        )
        
    def setup_content(self):
        """Add OpenAI-specific content"""
        # Cost display - use a size between primary and title
        self.cost_label = QLabel("$0.0000")
        font = QFont()
        font.setPointSize(20)  # Reduced from 24
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; font-weight: bold;")
        self.layout.addWidget(self.cost_label)
        
        # Add small spacing after price
        self.layout.addSpacing(3)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['secondary']}px;")
        self.layout.addWidget(self.token_label)
        
        # Add spacing before chart section
        self.layout.addSpacing(5)
        
        # Weekly chart label
        self.chart_label = QLabel("Past 7 days:")
        self.chart_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['small']}px;")
        self.layout.addWidget(self.chart_label)
        
        # Bar chart
        self.bar_chart = BarChartWidget()
        self.layout.addWidget(self.bar_chart)
        
    def update_display(self, data: Dict[str, Any]):
        """Update the card display"""
        cost = data.get('cost', 0.0)
        tokens = data.get('tokens')
        status = data.get('status', 'Active')
        weekly_data = data.get('weekly_data', {})
        
        # Update cost
        self.cost_label.setText(f"${cost:.4f}")
        
        # Update tokens
        if tokens is not None:
            self.token_label.setText(f"Tokens: {tokens:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        # Update weekly data if provided
        if weekly_data:
            self.update_weekly_data(weekly_data)
            
        # Update status
        status_type = "normal"
        if status == "Active" or "Session" in status:
            status_type = "active"
        elif "Waiting" in status:
            status_type = "warning"
        elif "Error" in status:
            status_type = "error"
            
        self.update_status(status, status_type)
            
    def update_weekly_data(self, weekly_data: Dict[str, Dict]):
        """Update the weekly bar chart data"""
        self.weekly_data = weekly_data
        
        # Extract costs for the chart
        chart_data = {}
        for date_str, data in weekly_data.items():
            chart_data[date_str] = data.get("cost", 0.0)
            
        self.bar_chart.set_data(chart_data)
        
        # Update chart label with total
        total_cost = sum(d.get("cost", 0) for d in weekly_data.values())
        total_tokens = sum(d.get("tokens", 0) for d in weekly_data.values())
        
        if total_cost > 0:
            self.chart_label.setText(f"Past 7 days: ${total_cost:.2f} ({total_tokens:,} tokens)")
        else:
            self.chart_label.setText("Past 7 days:")
            
    def scale_content_fonts(self, scale: float):
        """Scale OpenAI-specific fonts"""
        # Scale cost label - using custom 20pt base size
        font = QFont()
        font.setPointSize(int(20 * scale))
        self.cost_label.setFont(font)
        
        # Scale other labels
        self.token_label.setStyleSheet(f"color: #666; font-size: {int(self.base_font_sizes['secondary'] * scale)}px;")
        self.chart_label.setStyleSheet(f"color: #666; font-size: {int(self.base_font_sizes['small'] * scale)}px;")