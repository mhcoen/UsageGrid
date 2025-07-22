#!/usr/bin/env python3
"""
Screenshot version with fake data for demo purposes
"""
import sys
import os
from datetime import datetime, timedelta, timezone
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_modular import ModularMainWindow

class ScreenshotMainWindow(ModularMainWindow):
    """Main window with fake data for screenshots"""
    
    def __init__(self):
        super().__init__()
        # Disable real API calls
        self.api_timer.stop()
        self.claude_timer.stop()
        self.cleanup_timer.stop()
        
        # Set up fake data after a short delay
        QTimer.singleShot(100, self.inject_fake_data)
        
    def inject_fake_data(self):
        """Inject realistic fake data for screenshot"""
        # OpenAI - Show significant usage
        openai_data = {
            'cost': 12.4578,
            'tokens': 8426534,
            'weekly_data': {
                '2025-07-15': {'cost': 1.0234, 'tokens': 715234},
                '2025-07-16': {'cost': 1.3256, 'tokens': 889234},
                '2025-07-17': {'cost': 1.8134, 'tokens': 1256234},
                '2025-07-18': {'cost': 2.3456, 'tokens': 1534567},
                '2025-07-19': {'cost': 2.5234, 'tokens': 1667234},
                '2025-07-20': {'cost': 1.6789, 'tokens': 1178234},
                '2025-07-21': {'cost': 1.7475, 'tokens': 1185837},
            },
            'status': 'Active'
        }
        self.layout_manager.update_card_data('openai', openai_data)
        
        # Claude Code - Show high usage for Max5x plan (88k limit)
        claude_data = {
            'daily_cost': 34.67,
            'session_cost': 21.34,
            'tokens': 72384,  # 82% of 88k limit
            'is_active': True,
            'session_start': datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3, minutes=42),
            'initial_rate_data': [1200, 1450, 1300, 1600, 1800, 2100, 2300, 2500, 2400, 2600],
            'model_breakdown': {
                'claude-3-5-opus-20241022': {
                    'input_tokens': 52384,
                    'output_tokens': 8234,
                    'cache_creation_tokens': 5000,
                    'cache_read_tokens': 15000
                },
                'claude-3-5-sonnet-20241022': {
                    'input_tokens': 15234,
                    'output_tokens': 4532,
                    'cache_creation_tokens': 1000,
                    'cache_read_tokens': 3000
                }
            }
        }
        self.layout_manager.update_card_data('anthropic', claude_data)
        
        # OpenRouter - Show substantial usage
        openrouter_data = {
            'cost': 3.2834,
            'detailed_info': {
                'usage': 3.2834,
                'limit': 25.00,
                'limit_remaining': 21.7166,
                'is_free_tier': False,
                'rate_limit': {
                    'requests': 1000,
                    'requests_remaining': 743
                }
            },
            'status': 'Active'
        }
        self.layout_manager.update_card_data('openrouter', openrouter_data)
        
        # Gemini - Show moderate usage
        gemini_data = {
            'cost': 0.5423,
            'requests': 3456,
            'status': 'Updates are not in real time',
            'status_type': 'italic'
        }
        self.layout_manager.update_card_data('gemini', gemini_data)
        
        # GitHub - Keep existing functionality
        github_card = self.layout_manager.get_card('github')
        if github_card and hasattr(github_card, 'fetch_data'):
            data = github_card.fetch_data()
            self.layout_manager.update_card_data('github', data)
        
        # Update totals
        daily_total = 12.4578 + 3.2834 + 0.5423  # $16.2835
        self.daily_total_label.setText(f"Daily: ${daily_total:.4f}")
        self.monthly_total_label.setText("Subscriptions: $100/mo")  # Max5x plan
        self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.info_label.setText("Real-time API monitoring")


def main():
    """Main entry point for screenshot version"""
    app = QApplication(sys.argv)
    app.setApplicationName("UsageGrid")
    
    window = ScreenshotMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()