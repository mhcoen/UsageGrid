"""
Enhanced OpenAI card with bar chart visualization
"""
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base_card import BaseProviderCard
import math


class SparklineWidget(QWidget):
    """Sparkline widget with gradient fill for 30-day cost trend"""
    
    def __init__(self):
        super().__init__()
        self.data = []  # List of (date, value) tuples for last 30 days
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        self.text_color = QColor(180, 180, 180)  # Default text color
        self.provider_color = QColor("#00a67e")  # OpenAI green
        
        # Animation for current day pulse
        self._pulse_radius = 3
        self.pulse_animation = QPropertyAnimation(self, b"pulseRadius")
        self.pulse_animation.setDuration(2000)
        self.pulse_animation.setStartValue(3)
        self.pulse_animation.setEndValue(6)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.start()
        
    @pyqtProperty(float)
    def pulseRadius(self):
        return self._pulse_radius
    
    @pulseRadius.setter
    def pulseRadius(self, value):
        self._pulse_radius = value
        self.update()
        
    def set_data(self, daily_data: List[tuple]):
        """Set the data to display as list of (date, value) tuples"""
        self.data = daily_data[-30:]  # Keep last 30 days
        self.update()
        
    def paintEvent(self, event):
        """Paint the sparkline with gradient fill"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data or len(self.data) < 2:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Insufficient data")
            return
            
        # Calculate dimensions
        margin = 10
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        # Find min/max for scaling
        values = [v for _, v in self.data]
        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val if max_val > min_val else 1
        
        # Create points for the line
        points = []
        for i, (date, value) in enumerate(self.data):
            x = margin + (i / (len(self.data) - 1)) * width
            y = margin + height - ((value - min_val) / value_range) * height
            points.append(QPointF(x, y))
        
        # Create gradient fill
        gradient = QLinearGradient(0, margin, 0, margin + height)
        gradient.setColorAt(0, QColor(self.provider_color.red(), self.provider_color.green(), 
                                     self.provider_color.blue(), 80))
        gradient.setColorAt(1, QColor(self.provider_color.red(), self.provider_color.green(), 
                                     self.provider_color.blue(), 0))
        
        # Draw filled area
        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), margin + height)
        for point in points:
            fill_path.lineTo(point)
        fill_path.lineTo(points[-1].x(), margin + height)
        fill_path.closeSubpath()
        
        painter.fillPath(fill_path, QBrush(gradient))
        
        # Draw the smooth line
        pen = QPen(self.provider_color, 2)
        painter.setPen(pen)
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        # Create smooth curve through points using quadratic bezier
        for i in range(1, len(points)):
            p1 = points[i-1]
            p2 = points[i]
            
            # Control point for smooth curve
            cx = (p1.x() + p2.x()) / 2
            cy = (p1.y() + p2.y()) / 2
            
            path.quadTo(p1.x() + (cx - p1.x()) * 0.5, p1.y(),
                       cx, cy)
            path.quadTo(p2.x() - (p2.x() - cx) * 0.5, p2.y(),
                       p2.x(), p2.y())
        
        painter.drawPath(path)
        
        # Draw dots for each data point
        dot_pen = QPen(self.provider_color, 1)
        painter.setPen(dot_pen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        
        for i, point in enumerate(points):
            if i == len(points) - 1:  # Current day with pulse
                # Pulsing effect
                painter.setPen(QPen(self.provider_color, 2))
                painter.setBrush(QBrush(self.provider_color))
                painter.drawEllipse(point, self._pulse_radius, self._pulse_radius)
                
                # Inner white dot
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.drawEllipse(point, 2, 2)
            else:
                # Regular dots
                painter.setPen(dot_pen)
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.drawEllipse(point, 2, 2)
                
        # Draw start and end labels
        painter.setPen(QPen(self.text_color))
        painter.setFont(QFont("Arial", 8))
        
        # Start date
        if self.data:
            start_date = self.data[0][0]
            start_label = start_date.strftime("%m/%d")
            painter.drawText(int(margin - 5), int(margin + height + 15), start_label)
            
            # End date
            end_date = self.data[-1][0]
            end_label = end_date.strftime("%m/%d")
            text_width = painter.fontMetrics().horizontalAdvance(end_label)
            painter.drawText(int(self.width() - margin - text_width + 5), int(margin + height + 15), end_label)


class OpenAICard(BaseProviderCard):
    """Enhanced OpenAI provider card with sparkline visualization"""
    
    def __init__(self):
        self.daily_data = []  # List of (date, cost) tuples
        super().__init__(
            provider_name="openai",
            display_name="OpenAI",
            color="#00a67e"  # Teal green
        )
        self.billing_url = "https://platform.openai.com/usage"
        self.enable_billing_link()
        # Update every 5 minutes (default)
        
    def setup_content(self):
        """Add OpenAI-specific content"""
        # Cost display - use a size between primary and title
        self.cost_label = QLabel("$0.0000")
        font = QFont()
        font.setPointSize(14)  # Further reduced for better balance
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.cost_label)
        
        # Add small spacing after price
        self.layout.addSpacing(3)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet(f"font-size: {self.base_font_sizes['secondary']}px;")
        self.layout.addWidget(self.token_label)
        
        # Add spacing before chart section
        self.layout.addSpacing(5)
        
        # Sparkline label
        self.sparkline_label = QLabel("Last 30 days")
        self.sparkline_label.setStyleSheet(f"font-size: {self.base_font_sizes['small']}px; color: #888888;")
        self.layout.addWidget(self.sparkline_label)
        
        # Sparkline chart
        self.sparkline = SparklineWidget()
        self.layout.addWidget(self.sparkline)
        
        # Total cost label
        self.total_label = QLabel("")
        self.total_label.setStyleSheet(f"font-size: {self.base_font_sizes['secondary']}px; font-weight: bold;")
        self.layout.addWidget(self.total_label)
        
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
            
        # Update weekly data if provided (convert to daily for sparkline)
        if weekly_data:
            self.update_sparkline_data(weekly_data)
            
        # Update status
        status_type = "normal"
        if status == "Active" or "Session" in status:
            status_type = "active"
        elif "Waiting" in status:
            status_type = "warning"
        elif "Error" in status:
            status_type = "error"
            
        self.update_status(status, status_type)
            
    def update_sparkline_data(self, weekly_data: Dict[str, Dict]):
        """Update the sparkline with daily data"""
        # Convert weekly data to daily format for sparkline
        daily_list = []
        
        # Get today
        today = datetime.now().date()
        
        # Generate last 30 days of data
        for i in range(30):
            date = today - timedelta(days=29-i)
            date_str = date.isoformat()
            
            # Use actual data if available, otherwise 0
            if date_str in weekly_data:
                cost = weekly_data[date_str].get("cost", 0.0)
            else:
                cost = 0.0
                
            daily_list.append((date, cost))
        
        self.daily_data = daily_list
        self.sparkline.set_data(daily_list)
        
        # Update total label (last 30 days)
        total_cost = sum(cost for _, cost in daily_list)
        self.total_label.setText(f"${total_cost:.2f} total")
            
    def update_theme_colors(self, is_dark: bool):
        """Update chart colors based on theme"""
        if is_dark:
            self.sparkline.text_color = QColor(180, 180, 180)
            self.sparkline_label.setStyleSheet(f"font-size: {self.base_font_sizes['small']}px; color: #888888;")
        else:
            self.sparkline.text_color = QColor(100, 100, 100)
            self.sparkline_label.setStyleSheet(f"font-size: {self.base_font_sizes['small']}px; color: #666666;")
        self.sparkline.update()
            
    def scale_content_fonts(self, scale: float):
        """Scale OpenAI-specific fonts"""
        # Scale cost label - using custom 14pt base size
        font = QFont()
        font.setPointSize(int(14 * scale))
        self.cost_label.setFont(font)
        
        # Scale other labels
        self.token_label.setStyleSheet(f"font-size: {int(self.base_font_sizes['secondary'] * scale)}px;")
        self.sparkline_label.setStyleSheet(f"font-size: {int(self.base_font_sizes['small'] * scale)}px; color: #888888;")
        self.total_label.setStyleSheet(f"font-size: {int(self.base_font_sizes['secondary'] * scale)}px; font-weight: bold;")