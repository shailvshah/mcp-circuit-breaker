# Error Pattern Catalog

Comprehensive catalog of error patterns for semantic circuit breaker strategy.

## Table of Contents

- [HTTP Status Codes](#http-status-codes)
- [API-Specific Errors](#api-specific-errors)
- [Database Errors](#database-errors)
- [File System Errors](#file-system-errors)
- [Network Errors](#network-errors)

## HTTP Status Codes

### 4xx Client Errors (Usually Fatal - Block)

| Code | Pattern | Action | Reason |
|------|---------|--------|--------|
| 400 | `400 Bad Request` | block | Invalid request format, won't succeed on retry |
| 401 | `401 Unauthorized` | block | Authentication required, needs human intervention |
| 403 | `403 Forbidden` | block | Permission denied, won't change on retry |
| 404 | `404 Not Found` | block | Resource doesn't exist, retry won't help |
| 405 | `405 Method Not Allowed` | block | Wrong HTTP method, code bug |
| 409 | `409 Conflict` | block | Resource conflict, needs resolution |
| 410 | `410 Gone` | block | Resource permanently deleted |
| 422 | `422 Unprocessable Entity` | block | Validation failed, needs fix |
| 429 | `429 Too Many Requests` | block | Rate limited, needs backoff |

### 5xx Server Errors (Usually Transient - Warn or Allow)

| Code | Pattern | Action | Reason |
|------|---------|--------|--------|
| 500 | `500 Internal Server Error` | warn | May be transient, but could indicate bug |
| 502 | `502 Bad Gateway` | warn | Temporary proxy issue |
| 503 | `503 Service Unavailable` | block | Service down, needs time to recover |
| 504 | `504 Gateway Timeout` | warn | Temporary timeout, may succeed on retry |

## API-Specific Errors

### OpenAI API

```json
{
  "semantic_patterns": {
    "Rate limit reached": "block",
    "insufficient_quota": "block",
    "model_not_found": "block",
    "invalid_api_key": "block",
    "context_length_exceeded": "block",
    "invalid_request_error": "block",
    "engine_overloaded": "warn"
  }
}
```

### Anthropic Claude API

```json
{
  "semantic_patterns": {
    "rate_limit_error": "block",
    "overloaded_error": "warn",
    "invalid_request_error": "block",
    "authentication_error": "block",
    "permission_error": "block"
  }
}
```

### GitHub API

```json
{
  "semantic_patterns": {
    "API rate limit exceeded": "block",
    "Resource not accessible": "block",
    "Bad credentials": "block",
    "Not Found": "block",
    "Validation Failed": "block"
  }
}
```

### AWS API

```json
{
  "semantic_patterns": {
    "ThrottlingException": "block",
    "RequestLimitExceeded": "block",
    "AccessDeniedException": "block",
    "ResourceNotFoundException": "block",
    "InvalidParameterException": "block",
    "ServiceUnavailableException": "warn"
  }
}
```

## Database Errors

### PostgreSQL

```json
{
  "semantic_patterns": {
    "connection refused": "block",
    "authentication failed": "block",
    "database .* does not exist": "block",
    "relation .* does not exist": "block",
    "deadlock detected": "block",
    "duplicate key value": "block",
    "foreign key violation": "block",
    "too many connections": "warn"
  }
}
```

### MySQL

```json
{
  "semantic_patterns": {
    "Access denied": "block",
    "Unknown database": "block",
    "Table .* doesn't exist": "block",
    "Deadlock found": "block",
    "Duplicate entry": "block",
    "Too many connections": "warn",
    "Lock wait timeout": "warn"
  }
}
```

### MongoDB

```json
{
  "semantic_patterns": {
    "Authentication failed": "block",
    "not authorized": "block",
    "namespace .* not found": "block",
    "duplicate key error": "block",
    "connection refused": "block",
    "operation exceeded time limit": "warn"
  }
}
```

## File System Errors

### Common File Errors

```json
{
  "semantic_patterns": {
    "Permission denied": "block",
    "No such file or directory": "block",
    "File exists": "block",
    "Is a directory": "block",
    "Not a directory": "block",
    "Disk quota exceeded": "block",
    "Read-only file system": "block",
    "Too many open files": "warn"
  }
}
```

## Network Errors

### Connection Errors

```json
{
  "semantic_patterns": {
    "Connection refused": "block",
    "Connection reset": "warn",
    "Connection timeout": "warn",
    "Host not found": "block",
    "Network unreachable": "block",
    "SSL certificate verify failed": "block",
    "Name or service not known": "block",
    "Temporary failure in name resolution": "warn"
  }
}
```

## Pattern Matching Tips

### Use Specific Patterns First

**Good**:
```json
{
  "429 Too Many Requests": "block",
  "rate limit exceeded": "block",
  "quota exceeded": "block"
}
```

**Avoid**:
```json
{
  "error": "block"  // Too broad!
}
```

### Escape Special Regex Characters

**Good**:
```json
{
  "404 Not Found": "block",
  "database .* does not exist": "block"
}
```

**Avoid**:
```json
{
  "404.Not.Found": "block"  // Dots match any character!
}
```

### Use Case-Insensitive Matching

The semantic strategy uses `re.IGNORECASE`, so these patterns match:
- `Rate Limit Exceeded`
- `rate limit exceeded`
- `RATE LIMIT EXCEEDED`

### Test Your Patterns

Use Python's `re` module to test:

```python
import re

pattern = "rate limit exceeded"
error = "Error: Rate Limit Exceeded. Please try again later."

if re.search(pattern, error, re.IGNORECASE):
    print("Match!")
```

## Action Types

- **block**: Trip circuit immediately, prevent further executions
- **warn**: Log warning but don't trip circuit (future feature)
- **ignore**: Don't take any action (future feature)

Currently, only `block` is fully implemented.

## Building Your Own Catalog

1. **Monitor Errors**: Collect actual error messages from your system
2. **Classify**: Determine which are transient vs fatal
3. **Extract Patterns**: Find common substrings or regex patterns
4. **Test**: Verify patterns match expected errors
5. **Refine**: Adjust based on false positives/negatives
6. **Document**: Keep a record of why each pattern was added

## Example: Building an Error Catalog

```python
# Step 1: Collect errors from logs
errors = [
    "OpenAI API error: Rate limit reached for requests",
    "Error 429: Too many requests. Please slow down.",
    "API quota exceeded. Please upgrade your plan.",
]

# Step 2: Find common patterns
patterns = {
    "rate limit": "block",  # Matches first two
    "quota exceeded": "block",  # Matches third
}

# Step 3: Test
for error in errors:
    for pattern, action in patterns.items():
        if re.search(pattern, error, re.IGNORECASE):
            print(f"'{error}' matches '{pattern}' -> {action}")
```

## Recommended Starter Set

For most applications, start with this minimal set:

```json
{
  "semantic_patterns": {
    "rate limit": "block",
    "quota exceeded": "block",
    "401": "block",
    "403": "block",
    "404": "block",
    "429": "block",
    "authentication failed": "block",
    "permission denied": "block"
  }
}
```

Then expand based on your specific APIs and services.
