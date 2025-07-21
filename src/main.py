#!/usr/bin/env python3
"""
LLM Cost Monitor - Main entry point
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with simplified approach"""
    from PyQt6.QtWidgets import QApplication
    from src.ui.simple_main_window import SimpleMainWindow
    
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Cost Monitor")
    app.setOrganizationName("LLMCostMonitor")
    
    # Create and show window
    window = SimpleMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()