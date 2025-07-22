"""
Card registry for dynamic card creation based on configuration
"""
from typing import Dict, Type, Any, Optional
from PyQt6.QtWidgets import QWidget

from .cards.base_card import BaseProviderCard
from .cards.simple_card import SimpleCard
from .cards.openai_card import OpenAICard
from .cards.openrouter_card import OpenRouterCard
from .cards.claude_code_card import ClaudeCodeCard
from .cards.gemini_card import GeminiCard
from .cards.github_card import GitHubCard


class CardRegistry:
    """Registry for provider card types"""
    
    # Built-in card types
    _card_types: Dict[str, Type[BaseProviderCard]] = {
        'simple': SimpleCard,
        'openai': OpenAICard,
        'openrouter': OpenRouterCard,
        'claude_code': ClaudeCodeCard,
        'gemini': GeminiCard,
        'github': GitHubCard,
    }
    
    @classmethod
    def register_card(cls, card_type: str, card_class: Type[BaseProviderCard]):
        """Register a new card type"""
        cls._card_types[card_type] = card_class
        
    @classmethod
    def create_card(cls, provider_config: Dict[str, Any]) -> Optional[BaseProviderCard]:
        """Create a card instance from configuration"""
        card_type = provider_config.get('card_type', 'simple')
        
        if card_type not in cls._card_types:
            print(f"Unknown card type: {card_type}")
            return None
            
        card_class = cls._card_types[card_type]
        
        # Extract common parameters
        provider_name = provider_config.get('name')
        display_name = provider_config.get('display_name', provider_name.title())
        color = provider_config.get('color', '#666666')
        
        # Size configuration
        size = (220, 210)  # Default
        if 'size' in provider_config:
            if provider_config['size'] == 'half':
                size = (220, 104)  # Half height with 2px spacing = 210px total
            elif isinstance(provider_config['size'], list) and len(provider_config['size']) == 2:
                size = tuple(provider_config['size'])
                
        # Create card based on type
        if card_type == 'simple':
            # Simple card specific parameters
            metric_name = provider_config.get('metric_name', 'Tokens')
            show_estimated = provider_config.get('show_estimated', False)
            
            return SimpleCard(
                provider_name=provider_name,
                display_name=display_name,
                color=color,
                metric_name=metric_name,
                show_estimated=show_estimated,
                size=size
            )
            
        elif card_type == 'openai':
            return OpenAICard()
            
        elif card_type == 'openrouter':
            return OpenRouterCard(size=size)
            
        elif card_type == 'claude_code':
            return ClaudeCodeCard()
            
        elif card_type == 'gemini':
            return GeminiCard()
            
        elif card_type == 'github':
            return GitHubCard()
            
        else:
            # Generic card creation for custom types
            try:
                return card_class(
                    provider_name=provider_name,
                    display_name=display_name,
                    color=color,
                    size=size
                )
            except Exception as e:
                print(f"Error creating card {card_type}: {e}")
                return None
                
    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available card types"""
        return list(cls._card_types.keys())