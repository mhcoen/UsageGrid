# LLM Cost Monitor

A real-time cost monitoring dashboard for multiple LLM providers.

## Features

- Monitor costs across OpenAI, Anthropic, OpenRouter, HuggingFace, and more
- Real-time polling with configurable intervals
- Beautiful dashboard with spending trends and model breakdowns
- Support for multiple API keys per provider
- Historical data tracking with SQLite
- Cross-platform desktop application (Windows, macOS, Linux)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-cost-monitor.git
cd llm-cost-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The application reads API keys from environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-..."
export HUGGINGFACE_API_TOKEN="hf_..."
```

## Usage

```bash
python -m src.main
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type checking
mypy src/
```

## License

MIT License