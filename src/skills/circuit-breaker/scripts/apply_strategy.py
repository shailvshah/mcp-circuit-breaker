#!/usr/bin/env python3
"""
Standalone circuit breaker strategy application.

This script applies circuit breaker logic without MCP infrastructure.
Can be used for testing or standalone integration.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directories to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.models import CircuitState, ToolCallRecord
from core.strategies import (
    CoolOffStrategy,
    SemanticStrategy,
    StrategyContext,
    StrictStrategy,
)


class InMemoryStateRepo:
    """Simple in-memory state repository for standalone usage."""

    def __init__(self) -> None:
        self.states: Dict[str, CircuitState] = {}
        self.state_changes: Dict[str, datetime] = {}
        self.failures: Dict[str, int] = {}
        self.calls: Dict[str, list] = {}

    async def get_state(self, tool_name: str) -> CircuitState:
        return self.states.get(tool_name, CircuitState.CLOSED)

    async def set_state(self, tool_name: str, state: CircuitState) -> None:
        self.states[tool_name] = state
        self.state_changes[tool_name] = datetime.now()

    async def get_last_state_change(self, tool_name: str) -> Optional[datetime]:
        return self.state_changes.get(tool_name)

    async def get_recent_calls(self, tool_name: str, window_seconds: int) -> list:
        if tool_name not in self.calls:
            return []
        cutoff = datetime.now().timestamp() - window_seconds
        return [c for c in self.calls[tool_name] if c.timestamp.timestamp() > cutoff]

    async def increment_failures(self, tool_name: str) -> None:
        self.failures[tool_name] = self.failures.get(tool_name, 0) + 1

    async def get_consecutive_failures(self, tool_name: str) -> int:
        return self.failures.get(tool_name, 0)

    async def reset_failures(self, tool_name: str) -> None:
        self.failures[tool_name] = 0

    async def record_call(self, record: ToolCallRecord) -> None:
        if record.tool_name not in self.calls:
            self.calls[record.tool_name] = []
        self.calls[record.tool_name].append(record)


class SimpleSettings:
    """Simple settings class for standalone usage."""

    def __init__(self, config: Dict[str, Any]):
        self.cb_failure_threshold = config.get("failure_threshold", 5)
        self.cb_reset_timeout = config.get("reset_timeout", 60)
        self.cb_window_seconds = config.get("window_seconds", 60)
        self.cb_max_requests_per_window = config.get("max_requests_per_window", 10)
        self.cb_semantic_patterns = config.get("semantic_patterns", {})
        self.cb_strict_blocklist = config.get("strict_blocklist", [])


async def apply_strategy(
    tool_name: str,
    arguments: Dict[str, Any],
    config: Dict[str, Any],
    error: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Apply circuit breaker strategies to a tool call.

    Args:
        tool_name: Name of the tool to check
        arguments: Tool arguments
        config: Circuit breaker configuration
        error: Optional error message from previous execution

    Returns:
        Tuple of (should_allow, block_reason)
    """
    repo = InMemoryStateRepo()
    settings = SimpleSettings(config)

    context = StrategyContext(
        tool_name=tool_name,
        arguments=arguments,
        settings=settings,
        repo=repo,
        error=error,
    )

    # Initialize strategies based on config
    strategies = []
    strategy_names = config.get("strategies", ["cool-off"])

    if "strict" in strategy_names:
        strategies.append(StrictStrategy())
    if "semantic" in strategy_names:
        strategies.append(SemanticStrategy())
    if "cool-off" in strategy_names:
        strategies.append(CoolOffStrategy())

    # Check if any strategy blocks
    for strategy in strategies:
        block_reason = await strategy.should_block(context)
        if block_reason:
            return (False, block_reason)

    return (True, None)


async def main_async() -> int:
    """Main async entry point."""
    parser = argparse.ArgumentParser(
        description="Apply circuit breaker strategy to a tool call"
    )
    parser.add_argument("tool_name", help="Name of the tool to check")
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to configuration JSON file",
    )
    parser.add_argument(
        "--arguments",
        "-a",
        default="{}",
        help="Tool arguments as JSON string",
    )
    parser.add_argument(
        "--error",
        "-e",
        help="Error message to analyze (for semantic strategy)",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        with open(args.config, "r") as f:
            config = json.load(f)

        # Parse arguments
        arguments = json.loads(args.arguments)

        # Apply strategy
        should_allow, block_reason = await apply_strategy(
            args.tool_name, arguments, config, args.error
        )

        if should_allow:
            print(f"✓ Tool '{args.tool_name}' is allowed to execute")
            return 0
        else:
            print(f"✗ Tool '{args.tool_name}' is blocked:")
            print(f"  Reason: {block_reason}")
            return 1

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
