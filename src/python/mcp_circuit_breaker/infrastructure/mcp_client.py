import asyncio
import os
from typing import List, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, CallToolResult
from loguru import logger
from .config import Settings

class DownstreamClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        """Connects to the downstream MCP server using stdio."""
        env = os.environ.copy()
        if self.settings.downstream_env:
            env.update(self.settings.downstream_env)

        server_params = StdioServerParameters(
            command=self.settings.downstream_command,
            args=self.settings.downstream_args,
            env=env
        )

        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            self._read, self._write = stdio_transport
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(self._read, self._write)
            )
            await self._session.initialize()
            logger.info("Connected to downstream MCP server")
            
        except Exception as e:
            logger.error(f"Failed to connect to downstream server: {e}")
            raise

    async def list_tools(self) -> List[Tool]:
        if not self._session:
            raise RuntimeError("Not connected to downstream server")
        result = await self._session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict) -> CallToolResult:
        if not self._session:
            raise RuntimeError("Not connected to downstream server")
        return await self._session.call_tool(name, arguments)

    async def close(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            logger.info("Disconnected from downstream MCP server")
