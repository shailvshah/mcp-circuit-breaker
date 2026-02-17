from typing import List

from loguru import logger
from mcp.types import CallToolResult, TextContent, Tool
from mcp_circuit_breaker.application.circuit_breaker import CircuitBreakerService
from mcp_circuit_breaker.infrastructure.mcp_client import DownstreamClient


class ProxyService:
    def __init__(
        self, mcp_client: DownstreamClient, circuit_breaker: CircuitBreakerService
    ):
        self.client = mcp_client
        self.cb = circuit_breaker

    async def list_tools(self) -> List[Tool]:
        """Fetches tools from downstream."""
        return await self.client.list_tools()  # type: ignore[no-any-return]

    async def call_tool(self, name: str, arguments: dict) -> CallToolResult:
        """Intercepts and forwards tool calls."""

        # 1. Ask Circuit Breaker
        allowed = await self.cb.can_execute(name, arguments)
        if not allowed:
            logger.warning(f"Blocked call to {name}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=(
                            "I've stopped this execution to protect the system. "
                            "The tool has been failing repeatedly or hitting limits. "
                            "Please review the previous errors or wait a moment."
                        ),
                    )
                ],
                isError=True,
            )

        # 2. Forward to Downstream
        try:
            result: CallToolResult = await self.client.call_tool(name, arguments)

            # 3. Check for Application-Level Errors (e.g. isError field)
            if result.isError:
                error_text = "Unknown Error"
                if result.content and hasattr(result.content[0], "text"):
                    error_text = result.content[0].text

                await self.cb.record_failure(name, arguments, error_msg=error_text)
            else:
                await self.cb.record_success(name, arguments)

            return result  # type: ignore[no-any-return]

        except Exception as e:
            # Network/Protocol errors
            logger.error(f"Error calling downstream tool {name}: {e}")
            await self.cb.record_failure(name, arguments, error_msg=str(e))
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Circuit Breaker Proxy Error: {e}")
                ],
                isError=True,
            )
