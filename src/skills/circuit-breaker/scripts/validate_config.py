#!/usr/bin/env python3
"""
Standalone configuration validator for circuit breaker settings.

This script validates circuit breaker configurations without requiring MCP.
Can be used by the Anthropic Skills system or standalone.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, cast

# Add parent directories to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.validation import validate_strategy_config


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, "r") as f:
        return cast(Dict[str, Any], json.load(f))


def main() -> int:
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate circuit breaker configuration"
    )
    parser.add_argument("config_file", help="Path to configuration JSON file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed validation results"
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.config_file)

        if args.verbose:
            print(f"Loaded configuration from {args.config_file}")
            print(json.dumps(config, indent=2))
            print()

        # Validate configuration
        is_valid, errors = validate_strategy_config(config)

        if is_valid:
            print("✓ Configuration is valid!")
            return 0
        else:
            print("✗ Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config_file}' not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
