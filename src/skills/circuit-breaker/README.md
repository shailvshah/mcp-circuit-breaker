# Circuit Breaker Skill

An Anthropic Skill for implementing circuit breaker patterns in AI agent workflows.

## Overview

This skill provides circuit breaker functionality that can be used independently of the MCP (Model Context Protocol) infrastructure. It helps protect AI agents and applications from common failure modes like infinite retry loops, rate limit violations, and cascading failures.

## Features

- **Three Complementary Strategies**:
  - **Strict**: Policy-based firewall for blocking dangerous operations
  - **Semantic**: Intelligent error analysis to distinguish transient vs fatal errors
  - **Cool-Off**: Time-based circuit breaker with automatic recovery

- **Standalone Operation**: Works without MCP infrastructure
- **Validation Tools**: Validate configurations before deployment
- **Execution Tools**: Test circuit breaker logic standalone
- **Comprehensive Documentation**: Detailed patterns, error catalogs, and examples

## Installation

### For Claude Environments

1. Copy the `circuit-breaker` directory to your Claude skills folder
2. Claude will automatically discover and load the skill

### For Standalone Use

1. Ensure Python 3.10+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt  # From project root
   ```

3. The skill scripts can now be used directly

## Usage

### In Claude

Simply mention circuit breaker concepts in your conversation:

- "I need to implement retry logic for API calls"
- "How can I protect against rate limits?"
- "Help me set up error handling for my automation"

Claude will automatically trigger this skill and provide guidance.

### Standalone Validation

Validate a circuit breaker configuration:

```bash
python scripts/validate_config.py my_config.json
```

Example output:
```
✓ Configuration is valid!
```

### Standalone Execution

Test if a tool would be blocked:

```bash
python scripts/apply_strategy.py \
  --config my_config.json \
  write_file \
  --arguments '{"path": "/etc/passwd"}'
```

Example output:
```
✗ Tool 'write_file' is blocked:
  Reason: I can't execute the 'write_file' tool because it's restricted by your current security policy.
```

## Configuration

### Basic Example

```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 5,
  "reset_timeout": 60,
  "window_seconds": 60,
  "max_requests_per_window": 10
}
```

### Production Example

```json
{
  "strategies": ["strict", "semantic", "cool-off"],
  "strict_blocklist": ["^delete_.*", "^admin_.*"],
  "semantic_patterns": {
    "rate limit": "block",
    "401": "block",
    "404": "block"
  },
  "failure_threshold": 3,
  "reset_timeout": 30,
  "window_seconds": 60,
  "max_requests_per_window": 20
}
```

See `assets/config_template.json` for more templates.

## Documentation

- **[SKILL.md](SKILL.md)**: Main skill documentation with usage examples
- **[references/strategy_patterns.md](references/strategy_patterns.md)**: Detailed strategy patterns and configuration examples
- **[references/error_catalog.md](references/error_catalog.md)**: Comprehensive error pattern catalog
- **[assets/config_template.json](assets/config_template.json)**: Ready-to-use configuration templates

## Examples

### Protect OpenAI API Calls

```json
{
  "strategies": ["semantic", "cool-off"],
  "semantic_patterns": {
    "Rate limit reached": "block",
    "insufficient_quota": "block"
  },
  "failure_threshold": 3,
  "reset_timeout": 60
}
```

### Read-Only Mode

```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "^write_.*",
    "^delete_.*",
    "^update_.*"
  ]
}
```

### Database Protection

```json
{
  "strategies": ["strict", "semantic"],
  "strict_blocklist": ["^drop_.*", "^truncate_.*"],
  "semantic_patterns": {
    "connection refused": "block",
    "authentication failed": "block"
  }
}
```

## Integration with MCP

This skill shares core logic with the MCP Circuit Breaker server. If you need MCP integration, see the main project README.

## Development

The skill uses shared core logic from `src/core/`:
- `core.models`: Circuit state and record models
- `core.strategies`: Strategy implementations
- `core.validation`: Configuration validation

This ensures consistency between the skill and MCP implementations.

## Testing

Run validation on example configs:

```bash
# Test development config
python scripts/validate_config.py assets/config_template.json

# Test strict strategy
python scripts/apply_strategy.py \
  --config <(echo '{"strategies":["strict"],"strict_blocklist":["^delete_.*"]}') \
  delete_file
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'core'`:

1. Ensure you're running from the project root
2. Check that `src/core/` exists
3. Verify Python path includes the project root

### Validation Failures

If validation fails:

1. Check JSON syntax
2. Verify regex patterns are valid
3. Ensure numeric values are in valid ranges
4. See error messages for specific issues

## Contributing

This skill is part of the larger MCP Circuit Breaker project. Contributions welcome!

## License

Same as the main MCP Circuit Breaker project.
