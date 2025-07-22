"""
Theme manager for handling color themes
"""
from typing import Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import pyqtSignal, QObject


class ThemeManager(QObject):
    """Manages application themes"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, themes: Dict[str, Dict[str, str]], default_theme: str = "light"):
        super().__init__()
        self.themes = themes
        self.current_theme = default_theme
        self.theme_data = themes.get(default_theme, themes.get("light", {}))
        
    def set_theme(self, theme_name: str):
        """Set the current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme_data = self.themes[theme_name]
            self.theme_changed.emit(theme_name)
            return True
        return False
        
    def get_color(self, color_key: str, default: str = "#000000") -> str:
        """Get a color value from the current theme"""
        return self.theme_data.get(color_key, default)
        
    def apply_theme_to_app(self, app: QApplication):
        """Apply theme to the entire application"""
        style = f"""
        QMainWindow {{
            background-color: {self.get_color('background')};
        }}
        QLabel {{
            color: {self.get_color('text_primary')};
        }}
        """
        app.setStyleSheet(style)
        
    def get_card_style(self, border_color: str) -> str:
        """Get card styling for current theme"""
        return f"""
        QFrame {{
            background-color: {self.get_color('card_background')};
            border: 2px solid {border_color};
            border-radius: 10px;
        }}
        QFrame:hover {{
            background-color: {self.get_color('card_hover', self.get_color('card_background'))};
            border: 2px solid {border_color};
        }}
        QFrame > QLabel {{
            color: {self.get_color('text_primary')};
            border: none !important;
            background: transparent;
            padding: 0px;
        }}
        QFrame QLabel {{
            border: none !important;
        }}
        QFrame QWidget {{
            border: none !important;
            background: transparent;
        }}
        QFrame QProgressBar {{
            border: 1px solid #e0e0e0;
            background-color: #e0e0e0;
        }}
        """
        
    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        return list(self.themes.keys())