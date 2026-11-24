import json, os, datetime as dt
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from . import db, tools, llm
from .graph import graph, scan_message
from .browser_agent import fill_application
from .modules import LIVE, PLANNED

N8N = os.getenv("N8N_URL", "http://localhost:5678")
STATIC = Path(__file__).parent / "static"

@asynccontextmanager
async def lifespan(_):
    db.init()
    yield

app = FastAPI(title="LifeAgent API", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC), name="static")

def _ap(row):
    if row: row["payload"] = json.loads(row.pop("payload_json"))
    return row

@app.get("/portal")
def portal(): return FileResponse(STATIC / "portal.html")

@app.get("/api/health")
def health(): return {"ok": True, "llm": llm.available(), "mcp": os.getenv("USE_MCP") == "1"}

@app.get("/api/modules")
def modules(): return {"live": LIVE, "planned": [{k: v for k, v in m.items() if k != "keywords"} for m in PLANNED]}

# ---- users / vault / consent
@app.get("/api/users")
def users(): return db.q("SELECT id,name,country,language,occupation,guardian_user_id FROM users")

@app.get("/api/users/{uid}/vault")
def vault(uid: int):
    u = db.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
    if not u: raise HTTPException(404, "user not found")
    docs = db.q("SELECT id,doc_type,title,created_at FROM vault_docs WHERE user_id=?", (uid,))
    return {"profile": u, "documents": docs, "consent": tools.has_consent(uid, "vault:read")}

class ConsentIn(BaseModel): granted: bool
@app.put("/api/users/{uid}/consent")
def set_consent(uid: int, b: ConsentIn):
    db.x("INSERT INTO consents(user_id,scope,granted) VALUES(?,?,?) ON CONFLICT(user_id,scope) DO UPDATE SET granted=excluded.granted,updated_at=CURRENT_TIMESTAMP",
         (uid, "vault:read", int(b.granted)))
    tools.log_activity(uid, "Vault", f"Vault access {'granted' if b.granted else 'revoked'} by you")
    return {"consent": b.granted}

# ---- agent
class ChatIn(BaseModel):
    user_id: int
    message: str

@app.post("/api/agent/chat")
async def chat(b: ChatIn):
    u = db.q("SELECT language FROM users WHERE id=?", (b.user_id,), one=True)
    if not u: raise HTTPException(404, "user not found")
    out = await graph.ainvoke({"user_id": b.user_id, "message": b.message, "language": u["language"], "trace": []})
    return {k: out.get(k) for k in ("intent", "reply", "trace", "approval", "result")}

@app.get("/api/schemes/match")
def schemes(user_id: int): return tools.find_schemes(user_id)

class ScamIn(BaseModel):
    user_id: int
    text: str

@app.post("/api/scam/check")
async def scam_check(b: ScamIn):
    u = db.q("SELECT language FROM users WHERE id=?", (b.user_id,), one=True) or {"language": "en"}
    trace = []
    r, ap, reply = await scan_message(b.user_id, b.text, trace, u["language"])
    return {"result": r, "approval": ap, "reply": reply, "trace": trace}

# ---- approvals (confirm-before-acting)
@app.get("/api/approvals")
def approvals(user_id: int, status: str = "pending"):
    return [_ap(r) for r in db.q("SELECT * FROM approvals WHERE user_id=? AND status=? ORDER BY id DESC", (user_id, status))]

async def _n8n(path: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            return (await c.post(f"{N8N}/webhook/{path}", json=payload)).status_code < 300
    except Exception:
        return False

@app.post("/api/approvals/{aid}/approve")
async def approve(aid: int):
    ap = _ap(db.q("SELECT * FROM approvals WHERE id=?", (aid,), one=True))
    if not ap or ap["status"] != "pending": raise HTTPException(409, "not pending")
    uid, p, out = ap["user_id"], ap["payload"], {}
    if ap["kind"] == "apply_scheme":
        s = p["scheme"]
        res = await fill_application(p["form"], s)
        db.x("INSERT INTO applications(user_id,scheme_id,scheme_name,status,reference,form_json,screenshot,mode) VALUES(?,?,?,?,?,?,?,?)",
             (uid, s["id"], s["name"], "submitted", res["reference"], json.dumps(p["form"]), res["screenshot"], res["mode"]))
        tools.log_activity(uid, "Browser Agent", f"Submitted {s['name']}", f"Ref {res['reference']} ({res['mode']})", "done", 0)
        follow = (dt.date.today() + dt.timedelta(days=14)).isoformat()
        tools.add_deadline(uid, f"Check status: {s['name']} ({res['reference']})", follow, "application")
        sent = await _n8n("lifeagent-submitted", {"user_id": uid, "scheme_name": s["name"], "reference": res["reference"], "follow_up_date": follow})
        if not sent:  # n8n down: keep demo alive
            db.x("INSERT INTO notifications(user_id,channel,title,body) VALUES(?,?,?,?)",
                 (uid, "backend-fallback", f"Application submitted: {s['name']}", f"Reference {res['reference']}. Check status by {follow}."))
        out = {**res, "n8n": sent}
    elif ap["kind"] == "alert_guardian":
        sent = await _n8n("lifeagent-scam-alert", {"user_id": uid, **p})
        if not sent:
            db.x("INSERT INTO notifications(user_id,channel,title,body) VALUES(?,?,?,?)",
                 (p["guardian_id"], "backend-fallback", "Family alert: possible scam", f"Risk {p['risk_score']}/100. " + "; ".join(p["reasons"])))
        tools.log_activity(uid, "Family Agent", "Alerted your guardian", f"n8n={'ok' if sent else 'fallback'}")
        out = {"n8n": sent}
    db.x("UPDATE approvals SET status='approved',decided_at=CURRENT_TIMESTAMP WHERE id=?", (aid,))
    return {"status": "approved", **out}

@app.post("/api/approvals/{aid}/reject")
def reject(aid: int):
    ap = db.q("SELECT * FROM approvals WHERE id=?", (aid,), one=True)
    if not ap: raise HTTPException(404, "not found")
    db.x("UPDATE approvals SET status='rejected',decided_at=CURRENT_TIMESTAMP WHERE id=?", (aid,))
    tools.log_activity(ap["user_id"], "Approval Gate", f"You rejected: {ap['summary']}")
    return {"status": "rejected"}

# ---- history
@app.get("/api/applications")
def applications(user_id: int): return db.q("SELECT * FROM applications WHERE user_id=? ORDER BY id DESC", (user_id,))

@app.get("/api/activity")
def activity(user_id: int): return db.q("SELECT * FROM activity_log WHERE user_id=? ORDER BY id DESC LIMIT 100", (user_id,))

@app.post("/api/activity/{aid}/undo")
def undo(aid: int):
    a = db.q("SELECT * FROM activity_log WHERE id=?", (aid,), one=True)
    if not a or not a["undoable"] or a["status"] != "done": raise HTTPException(409, "cannot undo")
    if a["ref_table"] == "deadlines": db.x("DELETE FROM deadlines WHERE id=?", (a["ref_id"],))
    db.x("UPDATE activity_log SET status='undone' WHERE id=?", (aid,))
    tools.log_activity(a["user_id"], "Undo", f"Undid: {a['action']}")
    return {"status": "undone"}

@app.get("/api/deadlines")
def deadlines(user_id: int): return db.q("SELECT * FROM deadlines WHERE user_id=? ORDER BY due_date", (user_id,))

@app.get("/api/deadlines/due")  # polled by n8n daily digest
def due(days: int = 7):
    lim = (dt.date.today() + dt.timedelta(days=days)).isoformat()
    return {"items": db.q("SELECT d.*,u.name FROM deadlines d JOIN users u ON u.id=d.user_id WHERE d.due_date<=? ORDER BY d.due_date", (lim,))}

class NotifyIn(BaseModel):
    user_id: int
    title: str
    body: str = ""
    channel: str = "n8n"

@app.post("/api/notify")  # called by n8n
def notify(b: NotifyIn):
    return {"id": db.x("INSERT INTO notifications(user_id,channel,title,body) VALUES(?,?,?,?)", (b.user_id, b.channel, b.title, b.body))}

@app.get("/api/notifications")
def notifications(user_id: int): return db.q("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 30", (user_id,))
