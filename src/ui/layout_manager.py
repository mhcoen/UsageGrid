"""
Layout manager for configurable card layouts
"""
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from .cards.base_card import BaseProviderCard
from .cards.openai_card import OpenAICard
from .cards.openrouter_card import OpenRouterCard
from .cards.claude_code_card import ClaudeCodeCard
from .cards.github_card import GitHubCard
from .cards.gemini_card import GeminiCard
from .cards.simple_card import SimpleCard


class LayoutManager:
    """Manages card layout based on configuration"""
    
    def __init__(self, layout_config: Dict[str, Any]):
        self.layout_config = layout_config
        self.cards: Dict[str, BaseProviderCard] = {}
        
    def create_layout(self, parent: QWidget) -> QGridLayout:
        """Create the grid layout with cards based on configuration"""
        grid = QGridLayout()
        grid.setHorizontalSpacing(1)  # Reduced column gap by 50%
        grid.setVerticalSpacing(2)  # Keep vertical spacing at 2px
        
        # Process each card/stack in the configuration
        for card_config in self.layout_config.get('cards', []):
            position = card_config.get('position', [0, 0])
            row, col = position
            
            if 'stack' in card_config:
                # Create a vertical stack of cards
                stack_widget = QWidget()
                stack_layout = QVBoxLayout()
                stack_layout.setContentsMargins(0, 0, 0, 0)
                stack_layout.setSpacing(2)  # Reduced from 5 to 2
                
                for stack_card_config in card_config['stack']:
                    card = self._create_card(stack_card_config)
                    if card:
                        stack_layout.addWidget(card)
                        provider = stack_card_config.get('provider')
                        if provider:
                            self.cards[provider] = card
                            
                stack_widget.setLayout(stack_layout)
                grid.addWidget(stack_widget, row, col)
                
            else:
                # Create a single card
                card = self._create_card(card_config)
                if card:
                    grid.addWidget(card, row, col)
                    provider = card_config.get('provider')
                    if provider:
                        self.cards[provider] = card
                        
        return grid
        
    def _create_card(self, card_config: Dict[str, Any]) -> Optional[BaseProviderCard]:
        """Create a card from configuration"""
        # Add the provider name to the config
        if 'provider' in card_config and 'name' not in card_config:
            card_config['name'] = card_config['provider']
            
        # Create card based on type
        card_type = card_config.get('card_type', card_config.get('provider'))
        
        if card_type == 'openai':
            return OpenAICard()
        elif card_type == 'openrouter':
            size = (220, 210) if card_config.get('size') != 'half' else (220, 104)
            return OpenRouterCard(size=size)
        elif card_type == 'claude_code':
            return ClaudeCodeCard()
        elif card_type == 'github':
            return GitHubCard()
        elif card_type == 'gemini':
            return GeminiCard()
        elif card_type == 'simple':
            # For simple cards, pass configuration
            return SimpleCard(
                provider_name=card_config.get('provider', 'unknown'),
                display_name=card_config.get('display_name', 'Unknown'),
                color=card_config.get('color', '#666666'),
                metric_name=card_config.get('metric_name', 'Requests')
            )
        else:
            raise ValueError(f"Unknown card type: {card_type}")
        
    def get_card(self, provider: str) -> Optional[BaseProviderCard]:
        """Get a card by provider name"""
        return self.cards.get(provider)
        
    def get_all_cards(self) -> Dict[str, BaseProviderCard]:
        """Get all cards"""
        return self.cards
        
    def update_card_data(self, provider: str, data: Dict[str, Any]):
        """Update a specific card's data"""
        card = self.cards.get(provider)
        if card:
            card.update_display(data)
        else:
            import logging
            logging.getLogger(__name__).warning(f"No card found for provider: {provider}")