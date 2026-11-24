"""Start the server over stdio, list its tools and call list_events (read-only)."""

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parent
EXPECTED = {
    "search_emails",
    "read_email",
    "create_draft",
    "list_events",
    "find_free_slots",
    "create_event",
}


async def main() -> bool:
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", str(PROJECT), "server.py"],
        env={**os.environ, "GOOGLE_PRIVATE_DIR": r"C:\my-private"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            info = await session.initialize()
            print("Server:", info.serverInfo.name)

            tools = (await session.list_tools()).tools
            print(f"\nTools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            tools_ok = {tool.name for tool in tools} == EXPECTED
            print("Tool list:", "PASS" if tools_ok else "FAIL")

            print("\nlist_events(days_ahead=1):")
            result = await session.call_tool("list_events", {"days_ahead": 1})
            for item in result.content:
                print(" ", getattr(item, "text", item))
            if not result.isError and not result.content:
                print("  (no events)")
            print("list_events:", "FAIL" if result.isError else "PASS")
            return tools_ok and not result.isError


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(0 if asyncio.run(main()) else 1)
