import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8001/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            res = await s.call_tool("check_message", {
                "text": "Your bank account will be blocked, click here http://sbi-secure-login.xyz"})
            print(json.dumps(json.loads(res.content[0].text), indent=2))

            res = await s.call_tool("find_schemes", {"user_id": 1})
            print(json.dumps(json.loads(res.content[0].text), indent=2))

asyncio.run(main())