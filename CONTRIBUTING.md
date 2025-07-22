# Contributing to UsageGrid

First off, thank you for considering contributing to UsageGrid! It's people like you that make UsageGrid such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots if possible**
- **Include your configuration (OS, Python version, etc.)**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing style
6. Issue that pull request!

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/usagegrid.git
   cd usagegrid
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Run tests:
   ```bash
   python -m pytest
   ```

## Style Guidelines

### Python Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Documentation

- Use clear and concise language
- Include code examples where appropriate
- Update the README.md if you change functionality
- Comment your code where necessary

## Adding a New Provider

To add support for a new LLM provider:

1. Create a new adapter in `src/providers/`:
   ```python
   from .base import BaseProvider
   
   class YourProvider(BaseProvider):
       def fetch_usage(self):
           # Implementation
           pass
   ```

2. Create a card widget in `src/ui/cards/`:
   ```python
   from .base_card import BaseProviderCard
   
   class YourProviderCard(BaseProviderCard):
       def setup_content(self):
           # Add your UI elements
           pass
           
       def update_display(self, data):
           # Update the display
           pass
   ```

3. Add configuration to `config.json`:
   ```json
   {
     "position": [row, col],
     "provider": "your_provider",
     "card_type": "your_provider",
     "display_name": "Your Provider",
     "color": "#hexcolor"
   }
   ```

4. Update documentation

## Testing

- Write tests for any new functionality
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Test on multiple platforms if possible

## Questions?

Feel free to contact the maintainer:
- Michael Coen - mhcoen@gmail.com

Thank you for contributing!