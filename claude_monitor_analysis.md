# Claude-Code-Usage-Monitor Analysis Report

## Overview
The Claude-Code-Usage-Monitor is specifically designed to monitor Claude API usage by parsing JSONL files from the Claude Code app (stored in `~/.claude/projects/`). Here's how it differs from your current LLM cost monitoring implementation:

## Key Differences

### 1. Data Source & Parsing Logic
**Claude-Code-Usage-Monitor:**
- Reads JSONL files from `~/.claude/projects/` directory
- Parses Claude-specific JSONL format with fields like:
  - `timestamp`
  - `message_id`, `request_id` (for deduplication)
  - `input_tokens`, `output_tokens`, `cache_creation_tokens`, `cache_read_tokens`
  - `model` (e.g., "claude-3-opus", "claude-3-sonnet", etc.)
  - `cost_usd` (sometimes present in the data)

**Your Implementation:**
- Designed to poll multiple LLM provider APIs directly
- No file parsing - uses API endpoints for real-time data

### 2. Cost Calculation
**Claude-Code-Usage-Monitor:**
- Has hardcoded pricing for Claude models:
  ```python
  FALLBACK_PRICING = {
      "opus": {"input": 15.0, "output": 75.0, "cache_creation": 18.75, "cache_read": 1.5},
      "sonnet": {"input": 3.0, "output": 15.0, "cache_creation": 3.75, "cache_read": 0.3},
      "haiku": {"input": 0.25, "output": 1.25, "cache_creation": 0.3, "cache_read": 0.03}
  }
  ```
- Prices are per million tokens
- Supports cache tokens (creation and read) with different pricing
- Total cost: $7.28 shown in screenshot

**Your Implementation:**
- Would need to implement similar pricing logic per provider
- OpenAI doesn't have cache tokens concept

### 3. Time Period & Session Management
**Claude-Code-Usage-Monitor:**
- Uses **5-hour session blocks** as the primary time unit
- Not tied to billing cycles - just groups usage into 5-hour periods
- Default view shows last 96 hours (4 days) of data
- The $7.28 appears to be cumulative over the viewed period
- No monthly billing cycle concept

**Your Implementation:**
- Planned for 30-60 second polling intervals
- Would need different time aggregation logic

### 4. Token & Message Counting
**Claude-Code-Usage-Monitor:**
- Counts total tokens: 7,430 (as shown)
- Counts sent messages: 61 (as shown)
- Tracks per-model statistics within each session block
- Implements deduplication using `message_id:request_id` hash

**Your Implementation:**
- Would need similar aggregation logic per provider

### 5. Deduplication Logic
**Claude-Code-Usage-Monitor:**
```python
def _create_unique_hash(data):
    message_id = data.get("message_id") or (
        data.get("message", {}).get("id")
    )
    request_id = data.get("requestId") or data.get("request_id")
    return f"{message_id}:{request_id}" if message_id and request_id else None
```
- Prevents counting the same usage entry multiple times
- Important for file-based approach where files might be re-read

### 6. Key Architecture Patterns
**Claude-Code-Usage-Monitor:**
- **SessionAnalyzer**: Groups usage into 5-hour blocks
- **PricingCalculator**: Handles cost calculations with caching
- **DataReader**: Parses JSONL files with deduplication
- **BurnRateCalculator**: Calculates usage rate per minute/hour
- **P90Calculator**: For custom plan limits (calculates 90th percentile usage)

## Implementation Recommendations for Your Project

1. **For OpenAI Adapter:**
   - You'll need to map OpenAI's usage data format to a common structure
   - OpenAI likely provides: prompt_tokens, completion_tokens, total_tokens
   - No cache tokens for OpenAI

2. **For Anthropic Adapter:**
   - Could reuse much of the Claude-Code-Usage-Monitor logic
   - Parse similar token types including cache tokens
   - Use the same pricing structure

3. **Time Aggregation:**
   - Consider if 5-hour blocks make sense for your use case
   - Maybe use daily/hourly aggregations instead
   - Add proper monthly billing cycle tracking

4. **Deduplication:**
   - Important if you're storing historical data
   - Each provider might have different unique identifiers

5. **Cost Calculation:**
   - Create a unified pricing structure across providers
   - Account for different token types per provider
   - Consider storing prices in configuration rather than hardcoding

## Missing from Claude-Code-Usage-Monitor
- No direct API integration (file-based only)
- No multi-provider support
- No real-time updates (requires file changes)
- No billing cycle awareness
- UI is terminal-based (using Rich library)