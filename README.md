# UsageGrid

A beautiful, real-time desktop application for monitoring usage and costs across multiple LLM providers. Track your AI spending with style.

![UsageGrid](docs/images/screenshot.png)

## Features

### 🎯 Multi-Provider Support
- **OpenAI** - Real-time cost tracking with 7-day history visualization
- **Anthropic Claude** - Monitor Claude usage via Claude Code JSONL files
- **OpenRouter** - Track credits, rate limits, and usage
- **Google Gemini** - Monitor Vertex AI usage (requires Google Cloud setup)
- **GitHub** - Activity tracking with contribution heatmap

### 📊 Real-Time Monitoring
- Live cost updates every 30-60 seconds
- Beautiful bar charts and progress indicators
- Token usage tracking and predictions
- Session-based monitoring with 5-hour billing blocks
- Session start times rounded down to the nearest hour

### 🎨 Stunning Themes
- 13 built-in themes including Light, Dark, Solarized, Nord, Dracula, and more
- Theme-aware UI components with dynamic color adaptation
- Persistent theme selection between sessions
- Quick theme switching with keyboard shortcut (T)

### 💾 Smart Caching
- SQLite database for historical data
- Intelligent caching to reduce API calls
- Background data fetching for smooth UI

### 🔧 Highly Configurable
- Modular card-based layout
- Responsive design that adapts to window size
- Font scaling support (Ctrl+/- or Cmd+/-)
- Customizable polling intervals

### 🏗️ Expandable Modular Architecture
- Easy to add new LLM providers without modifying core code
- Plugin-style provider system with standardized interfaces
- Each provider is a self-contained module with its own adapter and UI card
- Theme-aware components that automatically adapt to user preferences
- Extensible layout system - arrange cards in any configuration

## Screenshots

[Screenshots will be added here]

## Installation

### Prerequisites
- Python 3.9 or higher
- PyQt6

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/usagegrid.git
cd usagegrid

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your API keys (see Configuration below)

# Run the application
python src/main_modular.py
```

## Configuration

### API Keys

Set your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# OpenRouter
export OPENROUTER_API_KEY="your-openrouter-api-key"

# GitHub (optional, for activity tracking)
export GITHUB_TOKEN="your-github-token"
export GITHUB_USERNAME="your-github-username"

# Google Cloud (for Gemini)
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Claude Code Setup

The app automatically reads Claude usage from JSONL files in:
- macOS/Linux: `~/.claude/projects/**/*.jsonl`
- Windows: `%USERPROFILE%\.claude\projects\**\*.jsonl`

No API key needed - it reads your local Claude Code usage files directly.

### Advanced Configuration

UsageGrid stores all personal data in `~/.usagegrid/`:
- `config.json` - User configuration and additional API keys
- `cache.db` - Historical data cache
- `logs/` - Application logs (if enabled)

Edit `~/.usagegrid/config.json` to customize:
- Additional API keys for each provider
- Claude subscription plan (pro/max5/max20)
- Default theme preference

Add multiple API keys per provider:
```json
{
  "providers": {
    "openai": {
      "additional_keys": ["sk-key1", "sk-key2"]
    }
  }
}
```

## Usage

### Keyboard Shortcuts
- **T** - Open theme selector
- **Ctrl/Cmd +** - Increase font size
- **Ctrl/Cmd -** - Decrease font size
- **Ctrl/Cmd 0** - Reset font size
- **Ctrl/Cmd Q** - Quit application

### Understanding the Display

#### OpenAI Card
- Shows current day's total cost
- 7-day bar chart with daily spending
- Token count for the day
- Updates every 5 minutes

#### Claude Code Card
- Current session cost and tokens
- Progress bars showing session time and token usage
- Prediction of when tokens will run out
- Model usage breakdown (Opus vs Sonnet)

#### OpenRouter Card
- Total usage and remaining credits
- Rate limit information
- Free tier status indicator

#### GitHub Card
- Today's commit count
- 4-month contribution heatmap
- PR/Issue counts
- Recent commits

## Architecture

The application follows an expandable modular architecture designed for easy extension:

```
src/
├── main_modular.py          # Main application window
├── core/
│   ├── database.py          # SQLite caching
│   └── polling_engine.py    # Async data fetching
├── providers/              # 🔌 EXPANDABLE: Add new providers here
│   ├── base.py             # Provider interface - inherit from this
│   ├── openai_adapter.py   # Example: OpenAI implementation
│   ├── openrouter_adapter.py
│   ├── gemini_adapter.py
│   └── claude_code_reader.py # Example: Local file reader
├── ui/
│   ├── theme_manager.py    # Theme system
│   ├── layout_manager.py   # Card layout system
│   └── cards/              # 🎨 EXPANDABLE: Add new card types here
│       ├── base_card.py    # Card interface - inherit from this
│       ├── openai_card.py  # Example: Chart visualization
│       ├── claude_code_card.py # Example: Progress bars
│       └── ...
└── utils/
    ├── credentials.py      # Secure credential management
    └── session_helper.py   # Claude session calculations
```

### Key Architecture Benefits:

- **🔌 Provider Independence**: Each provider is completely self-contained
- **🎨 UI Flexibility**: Cards can have completely different UIs while sharing common functionality
- **🔄 Hot-swappable**: Add/remove providers without touching core code
- **📦 Clean Separation**: Business logic (providers) separated from UI (cards)
- **🎯 Single Responsibility**: Each module has one clear purpose

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Creating a New Provider Card

1. Extend `BaseProviderCard` in `src/ui/cards/`
2. Implement `setup_content()` and `update_display()`
3. Add provider to layout configuration
4. Create adapter in `src/providers/` if needed

### Adding a New Theme

Add your theme to `config.json`:

```json
"themes": {
  "your_theme": {
    "name": "Your Theme",
    "background": "#color",
    "card_background": "#color",
    "text_primary": "#color",
    "text_secondary": "#color",
    "border": "#color",
    "accents": {
      "openai": "#color",
      "anthropic": "#color",
      // ... provider-specific colors
    }
  }
}
```

## Troubleshooting

### OpenAI Shows "Waiting for API reset"
- OpenAI has rate limits on their usage API
- Data will update when the rate limit resets

### Claude Code Shows No Data
- Ensure Claude Code is installed and has been used
- Check that JSONL files exist in `~/.claude/projects/`
- Sessions are 5-hour windows; new sessions start automatically

### Theme Changes Don't Persist
- Ensure the app has write permissions to `config.json`
- Check console for any error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Michael Coen**

- Email: mhcoen@gmail.com
- Email: mhcoen@alum.mit.edu
- GitHub: [@mhcoen](https://github.com/mhcoen)

## Acknowledgments

- Thanks to Claude, Gemini, and Zen for assistance during development
- Icons and color schemes inspired by the respective service providers
- Built with PyQt6 and Python

## Roadmap

- [ ] Add support for more LLM providers (Cohere, Hugging Face, etc.)
- [ ] Export data to CSV/JSON
- [ ] Cost alerts and notifications
- [ ] Historical trend analysis
- [ ] Team/organization support
- [ ] Mobile companion app

---

Made with ❤️ for the AI community