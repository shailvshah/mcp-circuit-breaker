import asyncio
import sys

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent, Tool

from .application.circuit_breaker import CircuitBreakerService
from .application.proxy_service import ProxyService
from .infrastructure.config import Settings
from .infrastructure.logger import configure_logger
from .infrastructure.mcp_client import DownstreamClient
from .infrastructure.memory_repo import InMemoryStateRepository


async def main() -> None:
    # 1. Setup
    try:
        settings = Settings()  # type: ignore[call-arg]
    except Exception as e:
        print(f"Failed to load settings: {e}", file=sys.stderr)
        sys.exit(1)

    configure_logger(settings)
    logger.info("Starting MCP Circuit Breaker...")

    # 2. Dependency Injection
    repo = InMemoryStateRepository()
    client = DownstreamClient(settings)
    circuit_breaker = CircuitBreakerService(repo, settings)
    proxy = ProxyService(client, circuit_breaker)

    # 3. Connect to Downstream
    try:
        await client.connect()
    except Exception:
        sys.exit(1)

    # 4. Initialize Server
    server = Server("mcp-circuit-breaker")

    # 5. Dynamic Tool Registration
    # Fetch tools from downstream and register them
    try:
        tools = await proxy.list_tools()
        logger.info(f"Discovered {len(tools)} tools from downstream.")
    except Exception as e:
        logger.error(f"Failed to list tools from downstream: {e}")
        await client.close()
        sys.exit(1)

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return tools  # type: ignore[no-any-return]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict
    ) -> list[TextContent | ImageContent | EmbeddedResource] | CallToolResult:
        result = await proxy.call_tool(name, arguments)
        return result  # type: ignore[no-any-return]

    # 6. Run Server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Circuit Breaker Server Ready (stdio)")
        try:
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
