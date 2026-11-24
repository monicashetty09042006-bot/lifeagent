"""Agents call tools here. With USE_MCP=1 the call goes over MCP (streamable HTTP) to
mcp_server/server.py; on any failure it falls back to a direct call so the demo never dies."""
import json, os
from . import tools

async def _mcp(name: str, args: dict):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(os.getenv("MCP_URL", "http://localhost:8001/mcp")) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(name, args)
            if res.isError:
                raise RuntimeError(res.content[0].text)
            return json.loads(res.content[0].text)

async def call(name: str, **args):
    if os.getenv("USE_MCP") == "1":
        try:
            out = await _mcp(name, args)
            out = out if isinstance(out, dict) else {"result": out}
            out["_via"] = "mcp"
            return out
        except Exception as e:
            print(f"[toolbus] MCP failed for {name}: {e}; using direct call")
    return getattr(tools, name)(**args)
