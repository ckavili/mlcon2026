"""Show real MCP tool discovery, schemas and deterministic results on stage."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client("http://127.0.0.1:8181/mcp") as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print("Discovered MCP tools:")
            for tool in tools:
                print(f"  {tool.name}: {(tool.description or '').splitlines()[0]}")
            selected = next(tool for tool in tools if tool.name == "calculate_dti")
            print("\nDTI tool input schema:")
            print(json.dumps(selected.inputSchema, indent=2))
            print("\nCall: calculate_dti(monthly_income=8500, monthly_debts=2400)")
            result = await session.call_tool("calculate_dti", {"monthly_income": 8500, "monthly_debts": 2400})
            if result.isError:
                raise RuntimeError(result)
            print("Result:", result.content[0].text)
            print("\nThis discovery and calculation used MCP over HTTP, with no model call.")


asyncio.run(main())
