#!/usr/bin/env python3
"""
Waterfall Chart Demo for OpenAI Cost Breakdown
Shows how costs accumulate across different models with cache savings
"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QRect, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, QPainterPath

class WaterfallBar:
    def __init__(self, label, value, start_y, color, is_negative=False):
        self.label = label
        self.value = value
        self.start_y = start_y
        self.end_y = start_y + value if not is_negative else start_y - abs(value)
        self.color = color
        self.is_negative = is_negative
        self.animated_height = 0
        
class WaterfallChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 300)
        
        # Data for the waterfall
        self.bars = []
        self.setup_data()
        
        # Animation properties
        self._current_bar = 0
        self._bar_progress = 0
        
        # Start animations after a short delay
        QTimer.singleShot(500, self.start_animation)
        
    def setup_data(self):
        # Define the waterfall data
        data = [
            ("Start", 0, QColor("#666666")),
            ("GPT-4", 3.45, QColor("#1976D2")),
            ("GPT-3.5", 1.23, QColor("#388E3C")),
            ("Embeddings", 0.18, QColor("#7B1FA2")),
            ("DALL-E 3", 0.84, QColor("#F57C00")),
            ("Cache Savings", -0.42, QColor("#00796B")),
        ]
        
        # Create bars
        current_y = 0
        for label, value, color in data:
            is_negative = value < 0
            bar = WaterfallBar(label, value, current_y, color, is_negative)
            self.bars.append(bar)
            if not is_negative:
                current_y += value
            else:
                current_y += value  # value is already negative
                
        # Add total bar
        total_bar = WaterfallBar("Total", current_y, 0, QColor("#D32F2F"))
        total_bar.end_y = current_y
        self.bars.append(total_bar)
        
    def start_animation(self):
        # Reset current bar
        self._current_bar = 1
        self._animation_step = 0
        
        # Create timer for sequential animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_next_bar)
        self.animation_timer.start(20)  # 50 FPS
        
    def animate_next_bar(self):
        if self._current_bar >= len(self.bars):
            self.animation_timer.stop()
            return
            
        # Animate current bar
        bar = self.bars[self._current_bar]
        if bar.animated_height < 1.0:
            # Ease out animation
            bar.animated_height = min(1.0, bar.animated_height + 0.05)
            self.update()
        else:
            # Move to next bar
            self._current_bar += 1
        
    @pyqtProperty(int)
    def barProgress(self):
        return self._bar_progress
        
    @barProgress.setter
    def barProgress(self, value):
        self._bar_progress = value
        if self._current_bar < len(self.bars):
            self.bars[self._current_bar].animated_height = value / 100.0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors and styling
        bg_color = QColor("#2b2b2b")
        text_color = QColor("#ffffff")
        grid_color = QColor("#444444")
        connector_color = QColor("#666666")
        
        # Dimensions
        margin = 50
        chart_width = self.width() - 2 * margin
        chart_height = self.height() - 2 * margin - 40
        
        # Find max value for scaling
        max_value = max(bar.end_y for bar in self.bars)
        if max_value == 0:
            max_value = 1  # Avoid division by zero
        
        bar_width = chart_width / (len(self.bars) + 1)
        bar_spacing = bar_width * 0.2
        actual_bar_width = bar_width * 0.6
        
        # Draw background
        painter.fillRect(self.rect(), bg_color)
        
        # Draw title
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.setPen(QPen(text_color, 1))
        painter.drawText(margin, 30, "OpenAI Cost Breakdown - Today")
        
        # Draw grid lines
        painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = margin + (i / 4) * chart_height
            painter.drawLine(margin, int(y), self.width() - margin, int(y))
            
            # Value labels
            value = max_value * (1 - i / 4)
            painter.setPen(QPen(text_color, 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(10, int(y) + 4, f"${value:.2f}")
            painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DotLine))
        
        # Draw bars
        painter.setFont(QFont("Arial", 10))
        
        for i, bar in enumerate(self.bars):
            if i == 0:  # Skip "Start" bar
                continue
                
            x = margin + i * bar_width + bar_spacing
            
            # Calculate positions based on animation
            if bar.label == "Total":
                # Total bar grows from bottom
                animated_height = chart_height * (bar.end_y / max_value) * bar.animated_height
                y1 = margin + chart_height
                y2 = margin + chart_height - animated_height
            else:
                # Regular bars grow from their start position
                bar_height = abs(bar.value) / max_value * chart_height
                animated_height = bar_height * bar.animated_height
                
                y1 = margin + chart_height - (bar.start_y / max_value * chart_height)
                if bar.is_negative:
                    y2 = y1 + animated_height
                else:
                    y2 = y1 - animated_height
            
            # Draw bar only if it has height
            if abs(y2 - y1) > 0.1:
                bar_rect = QRect(int(x), int(min(y1, y2)), int(actual_bar_width), int(abs(y2 - y1)))
                
                # Fill bar
                painter.fillRect(bar_rect, bar.color)
                
                # Draw bar outline
                painter.setPen(QPen(bar.color.darker(120), 2))
                painter.drawRect(bar_rect)
                
                # Draw connector lines for animated bars
                if i > 1 and i < len(self.bars) - 1 and self.bars[i-1].animated_height > 0.8:
                    painter.setPen(QPen(connector_color, 1, Qt.PenStyle.DashLine))
                    prev_x = margin + (i-1) * bar_width + bar_spacing + actual_bar_width
                    
                    # Find the y position to connect from
                    if bar.is_negative:
                        connect_y = margin + chart_height - (bar.start_y / max_value * chart_height)
                    else:
                        connect_y = y2
                    
                    painter.drawLine(int(prev_x), int(connect_y), int(x), int(connect_y))
                
                # Draw value on bar when animation is mostly complete
                if bar.animated_height > 0.8:
                    painter.setPen(QPen(text_color, 1))
                    painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    
                    value_text = f"${abs(bar.value):.2f}" if bar.label != "Total" else f"${bar.end_y:.2f}"
                    if bar.is_negative:
                        value_text = f"-{value_text}"
                        
                    fm = QFontMetrics(painter.font())
                    text_width = fm.horizontalAdvance(value_text)
                    text_x = x + (actual_bar_width - text_width) / 2
                    
                    if bar.is_negative:
                        text_y = y2 + 20
                    else:
                        text_y = y2 - 8
                        
                    painter.drawText(int(text_x), int(text_y), value_text)
            
            # Always draw labels
            painter.setPen(QPen(text_color, 1))
            painter.setFont(QFont("Arial", 9))
            fm = QFontMetrics(painter.font())
            label_width = fm.horizontalAdvance(bar.label)
            label_x = x + (actual_bar_width - label_width) / 2
            painter.drawText(int(label_x), self.height() - 20, bar.label)
        
        # Draw cache savings annotation when animation is complete
        if len(self.bars) > 5 and self.bars[5].animated_height > 0.9:
            painter.setFont(QFont("Arial", 10))
            painter.setPen(QPen(QColor("#00796B"), 1))
            painter.drawText(self.width() - 160, 35, "✓ Cache saved $0.42")

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAI Cost Waterfall Chart Demo")
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add waterfall chart
        self.waterfall = WaterfallChart()
        layout.addWidget(self.waterfall)
        
        # Add restart button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        restart_btn = QPushButton("Restart Animation")
        restart_btn.clicked.connect(self.restart_animation)
        button_layout.addWidget(restart_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(600, 400)
        
    def restart_animation(self):
        # Reset all bars
        for bar in self.waterfall.bars:
            bar.animated_height = 0
        self.waterfall._current_bar = 0
        self.waterfall._bar_progress = 0
        self.waterfall.update()
        
        # Restart animation
        if hasattr(self.waterfall, 'animation_timer'):
            self.waterfall.animation_timer.stop()
        self.waterfall.start_animation()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())