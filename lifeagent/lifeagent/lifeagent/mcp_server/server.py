"""LifeAgent MCP server. Same tools the LangGraph agents use, exposed over MCP so ANY client
(Claude Desktop, n8n MCP Client node, other agents) can drive LifeAgent.
  HTTP (default):  python mcp_server/server.py          -> http://localhost:8001/mcp
  stdio:           MCP_TRANSPORT=stdio python mcp_server/server.py"""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
from mcp.server.fastmcp import FastMCP
from app import tools, db

db.init()
mcp = FastMCP("lifeagent", host="0.0.0.0", port=int(os.getenv("MCP_PORT", "8001")))

@mcp.tool()
def get_profile(user_id: int) -> dict:
    """Read a user's vault profile. Returns {error:'consent_required'} if the user revoked vault access."""
    return tools.get_profile(user_id)

@mcp.tool()
def find_schemes(user_id: int) -> dict:
    """Find government schemes the user is eligible for, with explainable reasons."""
    return tools.find_schemes(user_id)

@mcp.tool()
def check_message(text: str) -> dict:
    """Scan a message or URL for phishing/scam signals. Returns risk_score 0-100, verdict, reasons, advice."""
    return tools.check_message(text)

@mcp.tool()
def add_deadline(user_id: int, title: str, due_date: str, source: str = "agent") -> dict:
    """Create a deadline reminder (ISO date). Logged and undoable."""
    return tools.add_deadline(user_id, title, due_date, source)

@mcp.tool()
def log_activity(user_id: int, agent: str, action: str, detail: str = "", status: str = "done",
                 undoable: int = 0, ref_table: str = "", ref_id: int = 0) -> dict:
    """Append to the user-visible activity log."""
    return tools.log_activity(user_id, agent, action, detail, status, undoable, ref_table, ref_id)

@mcp.tool()
def propose_action(user_id: int, kind: str, summary: str, payload: dict) -> dict:
    """Queue a consequential action for the user's approval. Never executes anything itself."""
    return tools.propose_action(user_id, kind, summary, payload)

@mcp.tool()
def record_scam_check(user_id: int, text: str, result: dict) -> dict:
    """Persist a scam-check result."""
    return tools.record_scam_check(user_id, text, result)

@mcp.resource("vault://{user_id}/profile")
def vault_profile(user_id: int) -> dict:
    """Vault profile as an MCP resource (consent enforced)."""
    return tools.get_profile(user_id)

if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "streamable-http"))
