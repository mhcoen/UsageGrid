"""
Layout manager for configurable card layouts
"""
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from .card_registry import CardRegistry
from .base_card import BaseProviderCard


class LayoutManager:
    """Manages card layout based on configuration"""
    
    def __init__(self, layout_config: Dict[str, Any]):
        self.layout_config = layout_config
        self.cards: Dict[str, BaseProviderCard] = {}
        
    def create_layout(self, parent: QWidget) -> QGridLayout:
        """Create the grid layout with cards based on configuration"""
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Process each card/stack in the configuration
        for card_config in self.layout_config.get('cards', []):
            position = card_config.get('position', [0, 0])
            row, col = position
            
            if 'stack' in card_config:
                # Create a vertical stack of cards
                stack_widget = QWidget()
                stack_layout = QVBoxLayout()
                stack_layout.setContentsMargins(0, 0, 0, 0)
                stack_layout.setSpacing(10)
                
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
            
        return CardRegistry.create_card(card_config)
        
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