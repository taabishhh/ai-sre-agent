import os
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.mcp_server import READ_TOOLS


@asynccontextmanager
async def mcp_session():
    # start our own mcp_server.py as a subprocess and talk to it over stdio
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent.mcp_server"],
        env=dict(os.environ),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_read_tools(session):
    # MCP tools map almost 1:1 to Claude's tool format
    resp = await session.list_tools()
    tools = []
    for tool in resp.tools:
        if tool.name in READ_TOOLS:
            schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None)
            tools.append({"name": tool.name, "description": tool.description or "", "input_schema": schema})
    return tools


async def call_tool(session, name, args):
    result = await session.call_tool(name, args)
    texts = [c.text for c in result.content if hasattr(c, "text")]
    return "\n".join(texts) if texts else str(result)


async def call_write_tool(name, args):
    async with mcp_session() as session:
        return await call_tool(session, name, args)
