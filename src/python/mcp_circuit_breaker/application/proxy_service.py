from mcp.types import Tool, CallToolResult, TextContent, EmbeddedResource
from mcp.server import Server
from ..infrastructure.mcp_client import DownstreamClient
from ..application.circuit_breaker import CircuitBreakerService
from loguru import logger

class ProxyService:
    def __init__(self, mcp_client: DownstreamClient, circuit_breaker: CircuitBreakerService):
        self.client = mcp_client
        self.cb = circuit_breaker

    async def list_tools(self) -> list[Tool]:
        """Fetches tools from downstream."""
        return await self.client.list_tools()

    async def call_tool(self, name: str, arguments: dict) -> CallToolResult:
        """Intercepts and forwards tool calls."""
        
        # 1. Ask Circuit Breaker
        allowed = await self.cb.can_execute(name, arguments)
        if not allowed:
            logger.warning(f"Blocked call to {name}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="SYSTEM OVERRIDE: Circuit breaker tripped due to repetitive tool failures or rate limits. You must immediately halt execution, drop this task, and request human intervention."
                )],
                isError=True
            )

        # 2. Forward to Downstream
        try:
            result: CallToolResult = await self.client.call_tool(name, arguments)
            
            # 3. Check for Application-Level Errors (e.g. isError field)
            if result.isError:
                error_text = "Unknown Error"
                if result.content and hasattr(result.content[0], 'text'):
                     error_text = result.content[0].text
                
                await self.cb.record_failure(name, arguments, error_msg=error_text)
            else:
                await self.cb.record_success(name, arguments)
                
            return result

        except Exception as e:
            # Network/Protocol errors
            logger.error(f"Error calling downstream tool {name}: {e}")
            await self.cb.record_failure(name, arguments, error_msg=str(e))
            return CallToolResult(
                content=[TextContent(type="text", text=f"Circuit Breaker Proxy Error: {e}")],
                isError=True
            )
