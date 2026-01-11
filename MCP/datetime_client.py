import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool
import json

params = StdioServerParameters(
    command="uv",
    args=["run", "datetime_server.py"],  
    env=None,
)

async def list_datetime_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools

async def call_datetime_tool(tool_name, tool_args):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            return await session.call_tool(tool_name, tool_args)

async def get_datetime_tools_openai():
    openai_tools = []

    for tool in await list_datetime_tools():
        schema = {**tool.inputSchema, "additionalProperties": False}

        openai_tools.append(
            FunctionTool(
                name=tool.name,
                description=tool.description,
                params_json_schema=schema,
                on_invoke_tool=lambda ctx, args, toolname=tool.name:
                    call_datetime_tool(toolname, json.loads(args))
            )
        )

    return openai_tools
