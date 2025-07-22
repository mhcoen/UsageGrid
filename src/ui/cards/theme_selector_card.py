"""
Theme selector card that temporarily replaces Gemini card
"""
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent
from typing import Dict, Any, List
from .base_card import BaseProviderCard


class ThemeSelectorCard(BaseProviderCard):
    """Theme selector card for choosing UI themes"""
    
    theme_selected = pyqtSignal(str)  # Emitted when a theme is selected
    close_requested = pyqtSignal()    # Emitted when user wants to close
    
    def __init__(self, themes: Dict[str, Dict], current_theme: str):
        self.themes = themes
        self.current_theme = current_theme
        self.original_theme = current_theme  # To restore if cancelled
        
        super().__init__(
            provider_name="theme_selector",
            display_name="Theme Selector",
            color="#795548",  # Brown
            size=(220, 104),  # Half-height like Gemini
            show_status=False  # No status for theme selector
        )
        
    def setup_content(self):
        """Setup theme selector content"""
        # Instructions label
        self.instruction_label = QLabel("↑↓ Navigate • Enter: Select • ESC: Cancel")
        self.instruction_label.setStyleSheet(f"color: #666; font-size: {self.base_font_sizes['small'] - 1}px;")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.instruction_label)
        
        # Theme list
        self.theme_list = QListWidget()
        self.theme_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.theme_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
                font-size: {self.base_font_sizes['secondary']}px;
                color: #333;
            }}
            QListWidget::item {{
                padding: 2px 5px;
                border: none;
                color: #333;
            }}
            QListWidget::item:selected {{
                background-color: rgba(41, 98, 255, 0.3);
                color: #2962FF;
            }}
            QListWidget::item:hover {{
                background-color: rgba(41, 98, 255, 0.15);
            }}
        """)
        
        # Populate theme list
        theme_order = [
            'light', 'dark', 'midnight', 'solarized', 'solarized_dark',
            'nord', 'dracula', 'material', 'material_dark', 'monokai',
            'github', 'github_dark', 'high_contrast'
        ]
        
        for theme_key in theme_order:
            if theme_key in self.themes:
                theme = self.themes[theme_key]
                item = QListWidgetItem(theme.get('name', theme_key.title()))
                item.setData(Qt.ItemDataRole.UserRole, theme_key)
                self.theme_list.addItem(item)
                
                # Select current theme
                if theme_key == self.current_theme:
                    self.theme_list.setCurrentItem(item)
        
        # Connect signals
        self.theme_list.currentItemChanged.connect(self.on_theme_hover)
        self.theme_list.itemActivated.connect(self.on_theme_selected)
        self.theme_list.itemClicked.connect(self.on_theme_selected)
        
        self.layout.addWidget(self.theme_list)
        
        # Make sure the list has focus
        self.theme_list.setFocus()
        
    def on_theme_hover(self, current, previous):
        """Preview theme on hover"""
        if current:
            theme_key = current.data(Qt.ItemDataRole.UserRole)
            self.theme_selected.emit(theme_key)
            
    def on_theme_selected(self, item):
        """Handle theme selection"""
        if item:
            theme_key = item.data(Qt.ItemDataRole.UserRole)
            self.current_theme = theme_key
            self.theme_selected.emit(theme_key)
            self.close_requested.emit()
            
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key presses"""
        if event.key() == Qt.Key.Key_Escape:
            # Restore original theme and close
            self.theme_selected.emit(self.original_theme)
            self.close_requested.emit()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Select current item
            current_item = self.theme_list.currentItem()
            if current_item:
                self.on_theme_selected(current_item)
        else:
            # Let the list handle arrow keys
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        """Don't emit clicked signal for theme selector"""
        # Override to prevent the base card click behavior
        pass
        
    def update_display(self, data: Dict[str, Any]):
        """Theme selector doesn't need display updates"""
        pass
        
    def scale_content_fonts(self, scale: float):
        """Scale fonts in theme selector"""
        self.instruction_label.setStyleSheet(f"color: #666; font-size: {int((self.base_font_sizes['small'] - 1) * scale)}px;")
        self.theme_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
                font-size: {int(self.base_font_sizes['secondary'] * scale)}px;
                color: #333;
            }}
            QListWidget::item {{
                padding: 2px 5px;
                border: none;
                color: #333;
            }}
            QListWidget::item:selected {{
                background-color: rgba(41, 98, 255, 0.3);
                color: #2962FF;
            }}
            QListWidget::item:hover {{
                background-color: rgba(41, 98, 255, 0.15);
            }}
        """)