"""Single source of truth for LifeAgent tools. Exposed to agents via toolbus and to any
MCP client via mcp_server/server.py."""
import json
from . import db, eligibility, scam

def has_consent(user_id: int, scope: str) -> bool:
    r = db.q("SELECT granted FROM consents WHERE user_id=? AND scope=?", (user_id, scope), one=True)
    return bool(r and r["granted"])

def get_profile(user_id: int) -> dict:
    if not has_consent(user_id, "vault:read"):
        return {"error": "consent_required", "scope": "vault:read"}
    u = db.q("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    if not u:
        return {"error": "not_found"}
    docs = db.q("SELECT doc_type,title,content_json FROM vault_docs WHERE user_id=?", (user_id,))
    u["documents"] = [{"doc_type": d["doc_type"], "title": d["title"], "content": json.loads(d["content_json"])} for d in docs]
    return u

def find_schemes(user_id: int) -> dict:
    p = get_profile(user_id)
    return p if "error" in p else eligibility.match(p)

def check_message(text: str) -> dict:
    return scam.analyze(text)

def log_activity(user_id: int, agent: str, action: str, detail: str = "", status: str = "done",
                 undoable: int = 0, ref_table: str = "", ref_id: int = 0) -> dict:
    i = db.x("INSERT INTO activity_log(user_id,agent,action,detail,status,undoable,ref_table,ref_id) VALUES(?,?,?,?,?,?,?,?)",
             (user_id, agent, action, detail, status, undoable, ref_table or None, ref_id or None))
    return {"id": i}

def add_deadline(user_id: int, title: str, due_date: str, source: str = "agent") -> dict:
    i = db.x("INSERT INTO deadlines(user_id,title,due_date,source) VALUES(?,?,?,?)", (user_id, title, due_date, source))
    log_activity(user_id, "Scheduler Agent", f"Added reminder: {title}", f"Due {due_date}", "done", 1, "deadlines", i)
    return {"id": i}

def propose_action(user_id: int, kind: str, summary: str, payload: dict) -> dict:
    """Human-in-the-loop gate: nothing consequential runs until the user approves this row."""
    i = db.x("INSERT INTO approvals(user_id,kind,summary,payload_json) VALUES(?,?,?,?)", (user_id, kind, summary, json.dumps(payload)))
    log_activity(user_id, "Approval Gate", f"Waiting for your approval: {summary}", "", "pending")
    return {"id": i, "kind": kind, "summary": summary, "payload": payload, "status": "pending"}

def record_scam_check(user_id: int, text: str, result: dict) -> dict:
    i = db.x("INSERT INTO scam_checks(user_id,input_text,risk_score,verdict,reasons_json) VALUES(?,?,?,?,?)",
             (user_id, text[:2000], result["risk_score"], result["verdict"], json.dumps(result["reasons"])))
    log_activity(user_id, "Scam Shield Agent", f"Checked a message: {result['verdict']} ({result['risk_score']}/100)")
    return {"id": i}
