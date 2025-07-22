# API Documentation

## Provider Adapters

### Base Provider

All provider adapters inherit from `BaseProvider`:

```python
class BaseProvider:
    def fetch_usage(self) -> Dict[str, Any]:
        """Fetch current usage data from the provider"""
        pass
```

### OpenAI Adapter

```python
from src.providers.openai_adapter import OpenAIAdapter

adapter = OpenAIAdapter(api_key="your-key")
data = adapter.fetch_usage()
# Returns: {"cost": 12.50, "tokens": 1000000, "status": "Active"}
```

### OpenRouter Adapter

```python
from src.providers.openrouter_adapter import OpenRouterAdapter

adapter = OpenRouterAdapter(api_key="your-key")
data = adapter.fetch_usage()
# Returns: {
#     "usage": 5.25,
#     "limit": 10.00,
#     "limit_remaining": 4.75,
#     "is_free_tier": False,
#     "rate_limit": {"requests": 200, "requests_remaining": 150}
# }
```

### Claude Code Reader

```python
from src.providers.claude_code_reader import ClaudeCodeReader

reader = ClaudeCodeReader()
data = reader.get_usage_data(since_date=datetime.now() - timedelta(hours=5))
# Returns: {
#     "total_cost": 2.50,
#     "model_breakdown": {
#         "claude-3-opus": {"input_tokens": 50000, "output_tokens": 2000},
#         "claude-3-sonnet": {"input_tokens": 30000, "output_tokens": 1000}
#     }
# }
```

## UI Components

### Theme Manager

```python
from src.ui.theme_manager import ThemeManager

themes = {...}  # Theme configuration
theme_manager = ThemeManager(themes, default_theme="light")

# Change theme
theme_manager.set_theme("dark")

# Get theme color
bg_color = theme_manager.get_color("background")

# Get accent color for provider
border_color = theme_manager.get_accent_color("openai", "#default")
```

### Layout Manager

```python
from src.ui.layout_manager import LayoutManager

layout_config = {...}  # Layout configuration
layout_manager = LayoutManager(layout_config)

# Get all cards
cards = layout_manager.get_all_cards()

# Update card data
layout_manager.update_card_data("openai", {"cost": 10.50})

# Get specific card
openai_card = layout_manager.get_card("openai")
```

### Provider Cards

All cards inherit from `BaseProviderCard`:

```python
from src.ui.cards.base_card import BaseProviderCard

class CustomCard(BaseProviderCard):
    def __init__(self):
        super().__init__(
            provider_name="custom",
            display_name="Custom Provider",
            color="#hexcolor"
        )
    
    def setup_content(self):
        """Add UI elements to the card"""
        self.cost_label = QLabel("$0.00")
        self.layout.addWidget(self.cost_label)
    
    def update_display(self, data: Dict[str, Any]):
        """Update the card with new data"""
        cost = data.get("cost", 0.0)
        self.cost_label.setText(f"${cost:.2f}")
```

## Database

### Cache Database

```python
from src.core.database import CacheDatabase

db = CacheDatabase()

# Store OpenAI usage
db.store_openai_usage(date="2025-01-22", tokens=50000, cost=1.25)

# Get historical data
history = db.get_openai_history(days=7)
# Returns: {"2025-01-22": {"tokens": 50000, "cost": 1.25}, ...}

# Store provider data
db.store_provider_data("openrouter", {"usage": 5.00, "limit": 10.00})

# Get provider data
data = db.get_provider_data("openrouter")
```

## Configuration

### Theme Configuration

```json
{
  "themes": {
    "custom_theme": {
      "name": "Custom Theme",
      "background": "#ffffff",
      "card_background": "#f0f0f0",
      "text_primary": "#000000",
      "text_secondary": "#666666",
      "border": "#cccccc",
      "accents": {
        "openai": "#00a67e",
        "anthropic": "#ff6b35"
      }
    }
  }
}
```

### Layout Configuration

```json
{
  "layout": {
    "rows": 2,
    "columns": 2,
    "cards": [
      {
        "position": [0, 0],
        "provider": "custom",
        "card_type": "custom",
        "display_name": "Custom",
        "color": "#hexcolor"
      }
    ]
  }
}
```