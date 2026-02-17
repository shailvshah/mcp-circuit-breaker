# Circuit Breaker Strategy Patterns

This document provides detailed patterns and examples for each circuit breaker strategy.

## Table of Contents

- [Strategy Selection Guide](#strategy-selection-guide)
- [Strict Strategy Patterns](#strict-strategy-patterns)
- [Semantic Strategy Patterns](#semantic-strategy-patterns)
- [Cool-Off Strategy Patterns](#cool-off-strategy-patterns)
- [Layered Defense Patterns](#layered-defense-patterns)

## Strategy Selection Guide

| Use Case | Recommended Strategy | Why |
|----------|---------------------|-----|
| Security Policy Enforcement | Strict | Deterministic, no false positives |
| API Rate Limit Protection | Semantic + Cool-Off | Detect rate limits early, backoff automatically |
| General Retry Protection | Cool-Off | Simple, effective for most cases |
| Production Critical Systems | All Three Layered | Defense in depth |
| Development/Testing | Cool-Off Only | Simpler, less restrictive |

## Strict Strategy Patterns

### Pattern 1: Read-Only Mode

**Use Case**: Allow read operations, block all writes

```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "^write_.*",
    "^delete_.*",
    "^update_.*",
    "^create_.*",
    "^modify_.*",
    "^remove_.*"
  ]
}
```

### Pattern 2: Database Protection

**Use Case**: Block dangerous database operations

```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "^drop_.*",
    "^truncate_.*",
    "execute_raw_sql",
    "run_migration"
  ]
}
```

### Pattern 3: File System Protection

**Use Case**: Prevent access to sensitive directories

```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "read_file.*etc/passwd",
    "read_file.*/etc/shadow",
    "write_file.*/system",
    "delete_file.*/usr"
  ]
}
```

### Pattern 4: Production Environment Lock

**Use Case**: Block all production modifications

```json
{
  "strategies": ["strict"],
  "strict_blocklist": [
    "deploy_to_production",
    "modify_production_.*",
    ".*_production_database"
  ]
}
```

## Semantic Strategy Patterns

### Pattern 1: API Error Detection

**Use Case**: Detect and handle common API errors

```json
{
  "strategies": ["semantic"],
  "semantic_patterns": {
    "rate limit exceeded": "block",
    "429 Too Many Requests": "block",
    "503 Service Unavailable": "block",
    "401 Unauthorized": "block",
    "403 Forbidden": "block",
    "404 Not Found": "block"
  }
}
```

### Pattern 2: OpenAI-Specific Errors

**Use Case**: Handle OpenAI API-specific error patterns

```json
{
  "strategies": ["semantic"],
  "semantic_patterns": {
    "Rate limit reached": "block",
    "insufficient_quota": "block",
    "model_not_found": "block",
    "invalid_api_key": "block",
    "context_length_exceeded": "block"
  }
}
```

### Pattern 3: Database Error Detection

**Use Case**: Detect fatal database errors

```json
{
  "strategies": ["semantic"],
  "semantic_patterns": {
    "connection refused": "block",
    "authentication failed": "block",
    "database does not exist": "block",
    "table .* does not exist": "block",
    "deadlock detected": "block"
  }
}
```

### Pattern 4: Network Error Classification

**Use Case**: Distinguish between transient and permanent network errors

```json
{
  "strategies": ["semantic"],
  "semantic_patterns": {
    "connection timeout": "warn",
    "temporary failure": "warn",
    "host not found": "block",
    "connection refused": "block",
    "certificate verify failed": "block"
  }
}
```

## Cool-Off Strategy Patterns

### Pattern 1: Aggressive Protection

**Use Case**: Quick response to failures, short recovery time

```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 2,
  "reset_timeout": 10,
  "window_seconds": 30,
  "max_requests_per_window": 5
}
```

**Behavior**: Trips after 2 failures, waits 10 seconds, allows max 5 requests per 30 seconds

### Pattern 2: Lenient Protection

**Use Case**: Allow more retries, longer recovery time

```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 10,
  "reset_timeout": 120,
  "window_seconds": 120,
  "max_requests_per_window": 50
}
```

**Behavior**: Trips after 10 failures, waits 2 minutes, allows max 50 requests per 2 minutes

### Pattern 3: Rate Limiting Focus

**Use Case**: Primarily concerned with request frequency

```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 100,
  "reset_timeout": 5,
  "window_seconds": 60,
  "max_requests_per_window": 10
}
```

**Behavior**: High failure tolerance, but strict rate limiting (10 req/min)

### Pattern 4: Failure Focus

**Use Case**: Primarily concerned with consecutive failures

```json
{
  "strategies": ["cool-off"],
  "failure_threshold": 3,
  "reset_timeout": 60,
  "window_seconds": 3600,
  "max_requests_per_window": 1000
}
```

**Behavior**: Low failure tolerance, but lenient rate limiting

## Layered Defense Patterns

### Pattern 1: Production API Gateway

**Use Case**: Comprehensive protection for production API calls

```json
{
  "strategies": ["strict", "semantic", "cool-off"],
  "strict_blocklist": [
    "^delete_.*",
    "^admin_.*"
  ],
  "semantic_patterns": {
    "rate limit": "block",
    "unauthorized": "block",
    "forbidden": "block",
    "not found": "block"
  },
  "failure_threshold": 3,
  "reset_timeout": 30,
  "window_seconds": 60,
  "max_requests_per_window": 20
}
```

### Pattern 2: Development Environment

**Use Case**: Balanced protection for development

```json
{
  "strategies": ["semantic", "cool-off"],
  "semantic_patterns": {
    "rate limit": "block",
    "quota exceeded": "block"
  },
  "failure_threshold": 5,
  "reset_timeout": 10,
  "window_seconds": 60,
  "max_requests_per_window": 30
}
```

### Pattern 3: High-Security Environment

**Use Case**: Maximum protection with strict policies

```json
{
  "strategies": ["strict", "semantic", "cool-off"],
  "strict_blocklist": [
    "^write_.*",
    "^delete_.*",
    "^execute_.*",
    "^run_.*"
  ],
  "semantic_patterns": {
    ".*error.*": "block",
    ".*failed.*": "block"
  },
  "failure_threshold": 1,
  "reset_timeout": 300,
  "window_seconds": 60,
  "max_requests_per_window": 5
}
```

## Best Practices

1. **Start Simple**: Begin with cool-off only, add complexity as needed
2. **Monitor and Tune**: Adjust thresholds based on actual error rates
3. **Test Thoroughly**: Verify circuit breaker behavior in staging
4. **Document Patterns**: Keep a catalog of error patterns you discover
5. **Layer Strategically**: Use strict for known risks, semantic for smart detection, cool-off as safety net
6. **Consider Recovery Time**: Set `reset_timeout` based on downstream service SLAs
7. **Balance Sensitivity**: Too sensitive = false positives, too lenient = missed failures
8. **Use Regex Carefully**: Test patterns thoroughly to avoid unintended matches

## Configuration Tips

- **failure_threshold**: Start with 3-5, adjust based on normal error rates
- **reset_timeout**: Match or exceed downstream service recovery time
- **window_seconds**: Use 60s for most cases, increase for bursty traffic
- **max_requests_per_window**: Calculate based on expected load and downstream limits
- **semantic_patterns**: Use specific patterns first, add broader patterns carefully
- **strict_blocklist**: Be explicit, avoid overly broad patterns
