"""
Core validation logic for circuit breaker configurations.

This module provides validation functions that can be used by both
MCP and Skills implementations.
"""

import re
from typing import Any, Dict, List, Tuple


def validate_strategy_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a circuit breaker configuration.

    Args:
        config: Configuration dictionary with strategy settings

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate strategies list
    if "strategies" in config:
        if not isinstance(config["strategies"], list):
            errors.append("'strategies' must be a list")
        else:
            valid_strategies = {"strict", "semantic", "cool-off"}
            for strategy in config["strategies"]:
                if strategy not in valid_strategies:
                    errors.append(
                        f"Unknown strategy '{strategy}'. " f"Valid: {valid_strategies}"
                    )

    # Validate strict blocklist
    if "strict_blocklist" in config:
        if not isinstance(config["strict_blocklist"], list):
            errors.append("'strict_blocklist' must be a list")
        else:
            for pattern in config["strict_blocklist"]:
                if not isinstance(pattern, str):
                    errors.append(
                        f"Blocklist pattern must be string, got {type(pattern)}"
                    )
                else:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        errors.append(f"Invalid regex pattern '{pattern}': {e}")

    # Validate semantic patterns
    if "semantic_patterns" in config:
        if not isinstance(config["semantic_patterns"], dict):
            errors.append("'semantic_patterns' must be a dictionary")
        else:
            for pattern, action in config["semantic_patterns"].items():
                try:
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"Invalid regex pattern '{pattern}': {e}")
                if action.lower() not in {"block", "warn", "ignore"}:
                    errors.append(
                        f"Invalid action '{action}'. " "Valid: block, warn, ignore"
                    )

    # Validate numeric thresholds
    numeric_fields = {
        "failure_threshold": (1, 100),
        "reset_timeout": (1, 3600),
        "window_seconds": (1, 3600),
        "max_requests_per_window": (1, 1000),
    }

    for field, (min_val, max_val) in numeric_fields.items():
        if field in config:
            value = config[field]
            if not isinstance(value, int):
                errors.append(f"'{field}' must be an integer")
            elif value < min_val or value > max_val:
                errors.append(f"'{field}' must be between {min_val} and {max_val}")

    return (len(errors) == 0, errors)


def validate_pattern(pattern: str) -> Tuple[bool, str]:
    """
    Validates a single regex pattern.

    Args:
        pattern: Regex pattern string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        re.compile(pattern)
        return (True, "")
    except re.error as e:
        return (False, f"Invalid regex: {e}")
