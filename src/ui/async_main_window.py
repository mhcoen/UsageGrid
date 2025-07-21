"""
Async-aware main window with thread-safe updates
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtGui import QFont, QPalette, QColor
import logging
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProviderUpdate:
    """Data class for provider updates"""
    provider_name: str
    cost: float
    status: str
    tokens: Optional[int] = None
    model_breakdown: Optional[Dict] = None


class AsyncWorker(QThread):
    """Worker thread for async operations"""
    provider_updated = pyqtSignal(ProviderUpdate)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, polling_engine, database):
        super().__init__()
        self.polling_engine = polling_engine
        self.database = database
        self.loop = None
        self.running = True
        
    def run(self):
        """Run async event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._run_polling())
        except Exception as e:
            logger.error(f"Worker thread error: {e}")
            self.error_occurred.emit(str(e))
            
    async def _run_polling(self):
        """Main polling loop"""
        # Initial delay to let everything initialize
        await asyncio.sleep(0.5)
        
        while self.running:
            try:
                # Get all provider statuses
                statuses = self.polling_engine.get_all_statuses()
                
                for name, status in statuses.items():
                    if status and status['last_data']:
                        update = ProviderUpdate(
                            provider_name=name,
                            cost=status['last_data'].total_cost,
                            status="Active",
                            tokens=status['last_data'].total_tokens,
                            model_breakdown=status['last_data'].model_breakdown
                        )
                    else:
                        update = ProviderUpdate(
                            provider_name=name,
                            cost=0.0,
                            status="Waiting..."
                        )
                    
                    # Emit update signal
                    self.provider_updated.emit(update)
                    
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
                
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)


class ProviderCard(QFrame):
    """Widget for displaying provider status with real-time updates"""
    clicked = pyqtSignal(str)
    
    def __init__(self, provider_name: str, display_name: str, color: str):
        super().__init__()
        self.provider_name = provider_name
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 160)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Provider name
        self.name_label = QLabel(display_name)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        self.name_label.setStyleSheet("color: #333; background-color: transparent;")
        layout.addWidget(self.name_label)
        
        # Cost display
        self.cost_label = QLabel("$0.00")
        font = QFont()
        font.setPointSize(20)
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet("color: #000; background-color: transparent; font-weight: bold;")
        layout.addWidget(self.cost_label)
        
        # Token count
        self.token_label = QLabel("Tokens: -")
        self.token_label.setStyleSheet("color: #666;")
        layout.addWidget(self.token_label)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet(f"""
            ProviderCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
            }}
            ProviderCard:hover {{
                background-color: #f8f9fa;
                border: 3px solid {color};
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.provider_name)
            
    @pyqtSlot(float, str, int)
    def update_data(self, cost: float, status: str, tokens: Optional[int] = None):
        """Update the displayed data (thread-safe)"""
        self.cost_label.setText(f"${cost:.2f}")
        self.status_label.setText(status)
        
        if tokens is not None:
            self.token_label.setText(f"Tokens: {tokens:,}")
        else:
            self.token_label.setText("Tokens: -")
        
        # Update status color
        if status == "Active":
            self.status_label.setStyleSheet("color: #28a745;")
        elif status == "Error":
            self.status_label.setStyleSheet("color: #dc3545;")
        else:
            self.status_label.setStyleSheet("color: gray;")


class AsyncMainWindow(QMainWindow):
    def __init__(self, database, polling_engine):
        super().__init__()
        self.db = database
        self.polling_engine = polling_engine
        self.provider_cards = {}
        self.worker = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("LLM Cost Monitor - Real-time")
        self.setMinimumSize(900, 650)
        
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
        font.setPointSize(26)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #28a745; font-size: 20px;")
        header_layout.addWidget(self.status_indicator)
        
        header_layout.addStretch()
        
        self.total_label = QLabel("Total: $0.00")
        font = QFont()
        font.setPointSize(20)
        self.total_label.setFont(font)
        header_layout.addWidget(self.total_label)
        
        layout.addLayout(header_layout)
        
        # Info bar
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Real-time polling active")
        self.info_label.setStyleSheet("color: #666; padding: 10px;")
        info_layout.addWidget(self.info_label)
        
        self.last_update_label = QLabel("Last update: Never")
        self.last_update_label.setStyleSheet("color: #666; padding: 10px;")
        info_layout.addStretch()
        info_layout.addWidget(self.last_update_label)
        
        layout.addLayout(info_layout)
        
        # Provider grid
        self.provider_grid = QGridLayout()
        self.provider_grid.setSpacing(20)
        layout.addLayout(self.provider_grid)
        
        layout.addStretch()
        
        # Status bar
        self.statusBar().showMessage("Initializing...")
        
        central_widget.setLayout(layout)
        
    def add_provider_card(self, provider_name: str, display_name: str, color: str):
        """Add a provider card to the display"""
        card = ProviderCard(provider_name, display_name, color)
        card.clicked.connect(self.on_provider_clicked)
        
        # Add to grid (2 columns)
        row = len(self.provider_cards) // 2
        col = len(self.provider_cards) % 2
        
        self.provider_grid.addWidget(card, row, col)
        self.provider_cards[provider_name] = card
        
    def start_async_polling(self):
        """Start the async polling worker"""
        if not self.worker:
            self.worker = AsyncWorker(self.polling_engine, self.db)
            self.worker.provider_updated.connect(self.handle_provider_update)
            self.worker.error_occurred.connect(self.handle_error)
            self.worker.start()
            
            self.statusBar().showMessage("Real-time polling active")
            self.status_indicator.setStyleSheet("color: #28a745; font-size: 20px;")
            
    @pyqtSlot(ProviderUpdate)
    def handle_provider_update(self, update: ProviderUpdate):
        """Handle provider update from worker thread"""
        if update.provider_name in self.provider_cards:
            card = self.provider_cards[update.provider_name]
            card.update_data(update.cost, update.status, update.tokens)
            
            # Update total
            self.update_total()
            
            # Update last update time
            from datetime import datetime
            self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            
    @pyqtSlot(str)
    def handle_error(self, error_msg: str):
        """Handle error from worker thread"""
        logger.error(f"Worker error: {error_msg}")
        self.statusBar().showMessage(f"Error: {error_msg}")
        self.status_indicator.setStyleSheet("color: #dc3545; font-size: 20px;")
        
    def update_total(self):
        """Update total cost display"""
        total = 0.0
        for card in self.provider_cards.values():
            try:
                cost_text = card.cost_label.text().replace("$", "")
                total += float(cost_text)
            except ValueError:
                pass
                
        self.total_label.setText(f"Total: ${total:.2f}")
        
    def on_provider_clicked(self, provider_name: str):
        """Handle provider card click"""
        card = self.provider_cards.get(provider_name)
        if card:
            status = card.status_label.text()
            tokens_text = card.token_label.text()
            cost_text = card.cost_label.text()
            
            QMessageBox.information(
                self,
                f"{provider_name.title()} Details",
                f"Status: {status}\n"
                f"Current Cost: {cost_text}\n"
                f"{tokens_text}\n\n"
                "Detailed views coming soon!"
            )
        
    def closeEvent(self, event):
        """Handle window close"""
        logger.info("Async main window closing")
        
        # Stop worker thread
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)  # Wait up to 2 seconds
            
        event.accept()