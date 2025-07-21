"""
Enhanced OpenAI card with bar chart visualization
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from datetime import datetime, timedelta
from typing import Dict, Optional


class BarChartWidget(QWidget):
    """Simple bar chart widget for displaying weekly data"""
    
    def __init__(self):
        super().__init__()
        self.data = {}  # {date_str: value}
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        
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


class OpenAICard(QFrame):
    """Enhanced OpenAI provider card with bar chart"""
    clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.provider_name = "openai"
        self.weekly_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(220, 280)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Provider name
        self.name_label = QLabel("OpenAI")
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
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.token_label)
        
        # Status
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Weekly chart label
        self.chart_label = QLabel("Past 7 days:")
        self.chart_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 8px;")
        layout.addWidget(self.chart_label)
        
        # Bar chart
        self.bar_chart = BarChartWidget()
        layout.addWidget(self.bar_chart)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            OpenAICard {
                background-color: white;
                border: 2px solid #10a37f;
                border-radius: 10px;
            }
            OpenAICard:hover {
                background-color: #f8f9fa;
            }
        """)
        
    def update_display(self, cost: float, tokens: Optional[int], status: str):
        """Update the basic display"""
        # Always show 4 decimal places for daily cost
        self.cost_label.setText(f"${cost:.4f}")
        
        if tokens is not None:
            self.token_label.setText(f"Tokens: {tokens:,}")
        else:
            self.token_label.setText("Tokens: -")
            
        self.status_label.setText(status)
        
        # Update status color
        if status == "Active" or "Session" in status:
            self.status_label.setStyleSheet("color: #28a745; font-size: 11px;")
        elif "Waiting" in status:
            self.status_label.setStyleSheet("color: #ff6b35; font-size: 11px; font-weight: bold;")
        elif "Error" in status:
            self.status_label.setStyleSheet("color: #dc3545; font-size: 11px;")
        else:
            self.status_label.setStyleSheet("color: gray; font-size: 11px;")
            
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
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)