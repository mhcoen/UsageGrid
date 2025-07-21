# LLM Cost Monitor Project

## Project Overview
A cross-platform desktop application to monitor real-time usage and costs across multiple LLM providers (OpenAI, Anthropic, OpenRouter, HuggingFace, and others). The app polls provider APIs every 30-60 seconds and displays spending data in an attractive dashboard.

## Key Design Decisions
- **Direct API approach**: No proxy servers or third-party services like LiteLLM
- **Modular provider system**: Each provider has its own adapter with customizable widgets
- **SQLite storage**: Lightweight local database for historical data
- **PyQt6 UI**: Native desktop app with modern styling
- **Async polling**: Concurrent API calls for real-time updates

## Architecture

### Provider Update Frequencies
- **OpenAI**: Near real-time (1-minute granularity available)
- **Anthropic**: Near real-time (minute-level granularity)
- **OpenRouter**: Real-time (usage data included in API responses)
- **HuggingFace**: Update frequency not specified in API docs

### UI Design
- **Adaptive layout**: Scales from single provider to grid view
- **Provider cards**: Clickable widgets with spending trends
- **Drill-down views**: Detailed model breakdowns and history
- **Modular components**: Configurable per-provider displays

## Implementation Plan

### Phase 1: Foundation (Core Infrastructure)
1. **Project Structure & Dependencies**
   - Create modular project structure
   - Set up virtual environment
   - Core deps: PyQt6, aiohttp, sqlite3, python-dotenv
   - Create requirements.txt and pyproject.toml

2. **Database Layer**
   - SQLite schema for providers, usage data, configurations
   - Database initialization and migration system
   - Async data access layer
   - Performance indexes for time-series queries

3. **Provider Abstraction**
   - Base `ProviderAdapter` abstract class
   - Standard interfaces for auth, polling, parsing
   - Shared utilities (rate limiting, retries)
   - Provider registry system

### Phase 2: Provider Implementations
4. **OpenAI Adapter** (start here - best documented)
5. **Anthropic Adapter**
6. **OpenRouter Adapter**
7. **HuggingFace Adapter**

Each adapter handles:
- Multi-key authentication
- API-specific data fetching
- Response normalization
- Error handling

### Phase 3: Polling System
8. **Async Polling Engine**
   - Configurable interval scheduler
   - Concurrent provider polling
   - Result queue system
   - State management
   - Graceful shutdown

### Phase 4: User Interface
9. **Base UI Window**
   - Main PyQt6 application window
   - Responsive layout system
   - Theme support (dark/light)
   - Navigation structure

10. **Provider Widget System**
    - Modular widget base class
    - Card-style provider displays
    - Real-time updates
    - Widget configuration

11. **Visualization Components**
    - Reusable graph components
    - Sparklines for cards
    - Time-series charts
    - Model breakdown charts

12. **Detail Views**
    - Provider drill-down panels
    - Tabbed data views
    - Model-specific breakdowns
    - API key management

### Phase 5: Features & Polish
13. **Settings & Configuration**
14. **Data Export** (CSV, JSON)
15. **Error Handling & Retry Logic**
16. **Logging & Debugging**

### Phase 6: Distribution
17. **Cross-Platform Packaging** (PyInstaller)
18. **Testing Suite**

## Development Progress

### Current Status
- Project planning completed
- Architecture designed
- Implementation plan created
- Ready to begin Phase 1

### Next Steps
1. Set up project structure
2. Create initial database schema
3. Build provider abstraction layer
4. Implement OpenAI adapter as proof of concept

## Technical Notes

### Database Schema (Planned)
```sql
providers (id, name, color, config_json)
api_keys (id, provider_id, key_hash, nickname)
usage_snapshots (timestamp, provider_id, api_key_id, cost, tokens, model, metadata_json)
daily_summaries (date, provider_id, total_cost, request_count)
```

### Provider Widget Configuration Example
```python
providers:
  openai:
    modules:
      - spending_trend: 
          default_range: "week"
      - model_breakdown:
          style: "horizontal_bars"
      - api_key_usage:
          show_percentages: true
```

## Updates Log
- 2025-07-20: Initial project planning and design completed
- 2025-07-20: Phase 1 completed - Project structure, database, and base classes created
- 2025-07-20: Basic UI window and polling engine implemented
- 2025-07-20: OpenAI provider adapter created (needs real API endpoint testing)
- 2025-07-21: Enhanced OpenRouter card to display all available API information
- 2025-07-20: Tested with real API endpoints - discovered actual API structures
- 2025-07-20: Implemented Claude Code JSONL reader for Anthropic usage data
- 2025-07-20: Created simplified synchronous version to avoid async/Qt issues
- 2025-07-20: Added Claude Code session tracking with time/token progress bars
- 2025-07-20: Fixed timezone issues and added accurate time calculations
- 2025-07-20: Added token usage prediction showing when tokens will run out
- 2025-07-20: Implemented background threading for JSONL file reading
- 2025-07-21: Enhanced UI with "Waiting for API reset" messages for rate limits
- 2025-07-21: Added weekly bar chart visualization for OpenAI usage history
- 2025-07-21: Implemented SQLite caching for OpenAI historical data
- 2025-07-21: Fixed Claude Code session time to use actual session start
- 2025-07-21: Updated all costs to show 4 decimal precision
- 2025-07-21: Removed seconds from time display for cleaner UI
- 2025-07-21: Fixed bar chart ordering to show chronological progression
- 2025-07-21: Created initial git repository and commit

## Current Status
- ✅ Project structure and dependencies
- ✅ SQLite database with schema
- ✅ Provider abstraction base class
- ✅ Basic polling engine
- ✅ Main UI window with provider cards
- ✅ OpenAI adapter with weekly bar chart visualization
- ✅ OpenRouter adapter with detailed API information display
- ✅ Anthropic adapter (via Claude Code JSONL reader)
- ✅ Real-time polling with actual cost data
- ✅ Claude Code enhanced card with session tracking
- ✅ Custom provider widgets (OpenAI, OpenRouter, Claude Code)
- ✅ SQLite caching for historical data
- ✅ Background threading for file operations
- ✅ Time/token progress bars with live updates
- ✅ Token usage prediction and session timing
- ✅ API rate limit handling with user-friendly messages
- ✅ OpenAI weekly bar chart visualization
- ✅ Database caching for historical data
- ✅ 4 decimal precision for all costs
- ✅ Clean time display without seconds
- ✅ Chronological bar chart ordering
- ⏳ Additional graphs and detailed views
- ⏳ Settings and configuration UI

## Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Run the application
python test_run.py
```

## Known Issues
- Gemini API requires Google Cloud setup with monitoring/billing APIs
- OpenAI API rate limits may cause "Waiting for API reset" messages
- Google Cloud API filter syntax needs adjustment for Gemini metrics

## API Findings (2025-07-20)

### OpenAI ✅
- **Endpoint**: `GET /v1/usage?date=YYYY-MM-DD`
- **Returns**: Token counts by timestamp and model
- **Cost Calculation**: Must calculate from token counts using pricing table
- **Data Available**: Context tokens, generated tokens, model, timestamp

### OpenRouter ✅  
- **Endpoints**: 
  - `GET /api/v1/auth/key` - Current usage and limits
  - `GET /api/v1/credits` - Total credits and usage
- **Returns**: Direct cost in USD
- **Data Available**: Usage amount, credit limit, remaining balance

### Anthropic ✅ (via Claude Code)
- **No Usage API**: All billing endpoints return 404
- **Alternative**: Implemented Claude Code JSONL reader
- **Data Source**: `~/.claude/projects/**/*.jsonl` files
- **Data Available**: Full usage with model, tokens, and timestamps

### HuggingFace ❌
- **No Billing API**: All attempted endpoints return 404
- **Alternative**: Would need different approach

## Implementation Notes
- Created `simple_main_window.py` for a non-async version that doesn't freeze
- The simple version shows provider cards and detects API keys
- Created proper async version with `async_main_window.py` and `main_async_clean.py`
- Async version uses worker thread for polling, avoiding UI freezing
- Real-time updates working with thread-safe signal/slot communication

## Running the Application

### Lightweight Version (Recommended):
```bash
# Set environment variables (optional)
export OPENAI_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"

# Run the lightweight version
python src/main_simple_lite.py
```

This version:
- Updates API providers every 5 minutes
- Updates Claude Code every 30 seconds using background threads
- Shows Claude Code session with live time/token tracking
- Displays "Claude Code: Max20x" with cleaner UI
- Shows "Waiting for API reset" for rate-limited providers
- OpenAI card includes 7-day bar chart of usage history (chronologically ordered)
- Caches OpenAI historical data in SQLite database
- Predicts when tokens will run out with exact time
- Shows when new Claude session starts
- Time displays show hours and minutes only (no seconds)
- All costs shown with 4 decimal precision (e.g., $0.0011)
- OpenRouter shows all API information (usage limit, rate limits, free tier status)
- Properly handles window closing without CPU spikes

### Original Version:
```bash
python test_real_simple.py
```

Note: The original version may lock up due to heavy JSONL processing.

## Todo List (Current State)
1. ✅ Set up project structure and core dependencies
2. ✅ Create database schema and SQLite initialization
3. ✅ Build provider abstraction base class
4. ✅ Implement OpenAI provider adapter
5. ✅ Implement Anthropic provider adapter (via Claude Code)
6. ✅ Implement OpenRouter provider adapter
7. ✅ Implement Gemini provider adapter (replaced HuggingFace)
8. ✅ Create polling engine with asyncio
9. ✅ Build base UI window and layout system
10. ✅ Test with real API endpoints
11. ✅ Add Claude Code JSONL file reader for Anthropic usage
12. ✅ Add Claude Code session tracking with progress bars
13. ✅ Fix timezone issues and time calculations
14. ✅ Add token usage prediction
15. ✅ Implement background threading for file operations
16. ✅ Add API rate limit handling with user messages
17. ✅ Create OpenAI weekly bar chart component
18. ✅ Add SQLite caching for OpenAI historical data
19. ✅ Fix session time calculation to use actual start
20. ✅ Update cost display to 4 decimal precision
21. ✅ Remove seconds from time display
22. ✅ Sort bar chart chronologically
23. ✅ Create initial git repository
24. ✅ Display all OpenRouter API information
25. ⏳ Add additional graph/chart components
25. ⏳ Add drill-down detail views
26. ⏳ Create settings/configuration UI
27. ⏳ Create modular provider widget system
28. ⏳ Add data export functionality
29. ⏳ Implement comprehensive error handling
30. ⏳ Add logging and debugging features
31. ⏳ Create packaging configuration for cross-platform
32. ⏳ Write tests for core functionality

## Project Structure
```
llm-costs/
├── src/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── main_simple_lite.py          # Lightweight version (recommended)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py              # SQLite operations
│   │   └── polling_engine.py        # Async polling system
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                  # Provider interface
│   │   ├── openai_adapter.py        # OpenAI implementation
│   │   ├── openrouter_adapter.py    # OpenRouter implementation
│   │   ├── gemini_adapter.py        # Gemini implementation
│   │   └── claude_code_reader.py    # Claude Code JSONL reader
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main window UI
│   │   ├── claude_code_card.py      # Enhanced Claude Code widget
│   │   └── openai_card.py           # OpenAI card with bar chart
│   └── utils/
│       ├── __init__.py
│       └── session_helper.py        # Claude session calculations
├── tests/
├── docs/
├── config.json                      # Claude Code plan configuration
├── CLAUDE.md                        # This file
├── README.md
├── requirements.txt
├── pyproject.toml
├── test_run.py                      # Test runner
├── .gitignore
└── .git/                            # Git repository (initialized)
```