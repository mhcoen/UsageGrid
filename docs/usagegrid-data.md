# UsageGrid Data Directory

All personal data for UsageGrid is stored in `~/.usagegrid/`

## Directory Structure

```
~/.usagegrid/
├── config.json     # User configuration (API keys, preferences)
├── cache.db        # SQLite database for historical data caching
└── logs/          # Application logs (if logging is enabled)
```

## Configuration File

The `config.json` file contains:

- **providers**: Additional API keys for each provider
- **claude_code**: Subscription plan settings
- **default_theme**: UI theme preference

### Example config.json:

```json
{
  "providers": {
    "openai": {
      "additional_keys": ["sk-key1", "sk-key2"]
    },
    "openrouter": {
      "additional_keys": []
    },
    "gemini": {
      "additional_keys": []
    }
  },
  "claude_code": {
    "subscription_plan": "max20"
  },
  "default_theme": "dark"
}
```

## Migration

When you first run UsageGrid after updating, it will automatically:

1. Create the `~/.usagegrid` directory if it doesn't exist
2. Migrate your existing `config.json` from the project directory
3. Migrate the cache database from the old location
4. Create a default config if none exists

## API Keys

API keys can be provided in two ways:

1. **Environment variables** (primary keys):
   - `OPENAI_API_KEY`
   - `OPENROUTER_API_KEY`
   - `GEMINI_API_KEY`

2. **config.json** (additional keys):
   - Add extra keys in the `providers` section
   - These are combined with environment keys
   - Useful for tracking multiple accounts/projects