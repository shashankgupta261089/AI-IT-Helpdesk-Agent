from pathlib import Path
import ast
import re
import sys
import asyncio
import threading

from langchain_mcp_adapters.client import MultiServerMCPClient


BASE_DIR = Path(__file__).resolve().parent
MCP_SERVER_PATH = BASE_DIR / "support_mcp_server.py"


def run_mcp_call(coro):
    """Run an MCP coroutine from scripts, notebooks, or Streamlit."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}

    def runner():
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result["value"]


def load_support_mcp_tools():
    """Load support ticket tools from the local stdio MCP server."""

    client = MultiServerMCPClient(
        {
            "support": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(MCP_SERVER_PATH)],
            }
        }
    )
    return run_mcp_call(client.get_tools())


def print_available_mcp_tools() -> list[str]:
    """Return MCP tool names for app diagnostics."""

    tools = load_support_mcp_tools()
    return [tool.name for tool in tools]


def format_mcp_tool_result(result) -> str:
    """Convert MCP content objects into a clean user-facing string."""

    if isinstance(result, str):
        try:
            parsed_result = ast.literal_eval(result)
        except (SyntaxError, ValueError):
            text_match = re.search(r"['\"]text['\"]\s*:\s*['\"]([^'\"]+)['\"]", result)
            if text_match:
                return text_match.group(1).strip()
            return result.strip()
        return format_mcp_tool_result(parsed_result)

    if isinstance(result, list):
        text_parts = []
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
            elif hasattr(item, "text"):
                text_parts.append(str(item.text))
            else:
                text_parts.append(str(item))
        return "\n".join(part for part in text_parts if part).strip()

    if isinstance(result, dict) and result.get("type") == "text":
        return str(result.get("text", "")).strip()

    if hasattr(result, "text"):
        return str(result.text).strip()

    return str(result)


def invoke_support_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Invoke one support MCP tool by name and return its text result."""

    tools = load_support_mcp_tools()
    for tool in tools:
        if tool.name == tool_name:
            result = run_mcp_call(tool.ainvoke(arguments))
            return format_mcp_tool_result(result)
    available = ", ".join(sorted(tool.name for tool in tools))
    raise RuntimeError(f"MCP tool '{tool_name}' was not found. Available tools: {available}")
