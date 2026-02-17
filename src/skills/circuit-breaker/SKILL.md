---
name: circuit-breaker
description: |
  Provides circuit breaker pattern implementation for preventing infinite loops,
  rate limiting, and intelligent error handling in AI agent workflows. Use this
  skill when implementing retry logic, protecting against runaway automation,
  analyzing error patterns, or setting up rate limiting policies. Supports three
  strategies: strict (policy enforcement), semantic (error analysis), and cool-off
  (temporal backoff). Trigger when user mentions: retry logic, rate limiting, error
  handling, infinite loops, API protection, or circuit breaker patterns.
---

# Circuit Breaker Skill

This skill helps you implement circuit breaker patterns to protect AI agents and applications from common failure modes like infinite retry loops, rate limit violations, and cascading failures.

## When to Use This Skill

Trigger this skill when the user needs help with:

- **Retry Logic**: Implementing smart retry mechanisms for API calls or operations
- **Rate Limiting**: Preventing excessive requests that could trigger rate limits
- **Error Handling**: Analyzing error patterns to determine if errors are transient or fatal
- **Infinite Loop Protection**: Detecting and breaking out of runaway automation
- **API Protection**: Safeguarding downstream services from overload
- **Failure Recovery**: Implementing graceful degradation and recovery strategies

## Available Strategies

The circuit breaker supports three complementary strategies that can be layered for defense-in-depth:

### 1. Strict Strategy (Policy Enforcement)

**Purpose**: Firewall-style blocking based on tool names or argument patterns.

**When to use**:
- Enforcing security policies (e.g., "no write operations")
- Blocking specific dangerous tools
- Implementing compliance requirements

**Configuration**:
```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "^delete_.*",
    "^drop_.*",
    "write_to_production"
  ]
}
```

**Behavior**: Blocks execution immediately before the tool is called. Never resets automatically.

### 2. Semantic Strategy (Error Analysis)

**Purpose**: Analyzes error messages to distinguish between transient and fatal errors.

**When to use**:
- Detecting rate limit errors that need long backoffs
- Identifying authentication failures that require human intervention
- Recognizing permanent errors (404, 401) vs temporary ones (503, 429)

**Configuration**:
```json
{
  "strategies": ["semantic"],
  "semantic_patterns": {
    "rate limit exceeded": "block",
    "429 Too Many Requests": "block",
    "401 Unauthorized": "block",
    "404 Not Found": "block"
  }
}
```

**Behavior**: Analyzes errors after execution. Trips circuit immediately when fatal patterns match, bypassing failure thresholds.

### 3. Cool-Off Strategy (Temporal Backoff)

**Purpose**: Time-based circuit breaker with failure counting and automatic recovery.

**When to use**:
- General protection against retry loops
- Rate limiting based on request frequency
- Automatic recovery after temporary failures

**Configuration**:
```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 5,
  "reset_timeout": 60,
  "window_seconds": 60,
  "max_requests_per_window": 10
}
```

**Behavior**:
- Counts consecutive failures
- Opens circuit after threshold is reached
- Waits for `reset_timeout` seconds
- Transitions to HALF_OPEN for trial
- Closes circuit on success

## Layered Defense Pattern

For production systems, combine all three strategies in priority order:

```json
{
  "strategies": ["strict", "semantic", "cool-off"],
  "strict_blocklist": ["^delete_.*"],
  "semantic_patterns": {
    "rate limit": "block",
    "unauthorized": "block"
  },
  "failure_threshold": 3,
  "reset_timeout": 30
}
```

**Execution order**:
1. **Strict** checks first (highest priority) - blocks dangerous tools
2. **Semantic** analyzes errors after execution - trips on fatal errors
3. **Cool-Off** provides safety net - catches everything else

## Usage Examples

### Example 1: Protecting API Calls

**User**: "I need to call the OpenAI API repeatedly but want to avoid hitting rate limits"

**Response**:
```python
# Use semantic strategy to detect rate limit errors
config = {
    "strategies": ["semantic", "cool-off"],
    "semantic_patterns": {
        "rate_limit_exceeded": "block",
        "429": "block"
    },
    "failure_threshold": 3,
    "reset_timeout": 60
}

# The circuit breaker will:
# 1. Detect rate limit errors immediately
# 2. Trip the circuit to prevent further calls
# 3. Wait 60 seconds before retrying
```

### Example 2: File Processing with Error Handling

**User**: "Process 1000 files but stop if there are too many errors"

**Response**:
```python
# Use cool-off strategy with low threshold
config = {
    "strategies": ["cool-off"],
    "failure_threshold": 5,
    "reset_timeout": 10
}

# The circuit breaker will:
# 1. Count consecutive failures
# 2. Stop processing after 5 failures
# 3. Allow retry after 10 seconds
```

### Example 3: Security-Constrained Operations

**User**: "Allow read operations but block all write operations"

**Response**:
```python
# Use strict strategy for policy enforcement
config = {
    "strategies": ["strict"],
    "strict_blocklist": [
        "^write_.*",
        "^delete_.*",
        "^update_.*",
        "^create_.*"
    ]
}

# The circuit breaker will:
# 1. Block any tool matching the patterns
# 2. Return security policy violation message
# 3. Never allow these operations
```

## Validation

Use the validation script to check your configuration:

```bash
python scripts/validate_config.py config.json
```

## Circuit States

The circuit breaker operates in three states:

- **CLOSED**: Normal operation, requests flow through
- **OPEN**: Circuit tripped, requests blocked
- **HALF_OPEN**: Testing recovery, allowing trial requests

## Best Practices

1. **Start Simple**: Begin with cool-off strategy, add semantic/strict as needed
2. **Tune Thresholds**: Adjust `failure_threshold` based on your use case
3. **Layer Strategies**: Use strict for known bad patterns, semantic for smart analysis, cool-off as safety net
4. **Monitor Patterns**: Review error logs to identify patterns for semantic strategy
5. **Test Recovery**: Ensure your `reset_timeout` allows sufficient recovery time

## Advanced Topics

For detailed information on:
- Error pattern catalogs → See `references/error_catalog.md`
- Strategy pattern examples → See `references/strategy_patterns.md`
- Configuration templates → See `assets/config_template.json`

## Integration

This skill can be used:
- **Standalone**: Using the validation and execution scripts
- **With MCP**: As a middleware server for Model Context Protocol
- **In Code**: Importing the core circuit breaker logic

See the skill README for installation and integration instructions.
