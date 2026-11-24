# LifeAgent — one personal agent for your whole day
> "Tell it your goal. It does the work, and you stay in control."

**Live agents (2):** Government & Benefits (agentic browser) · Safety & Scam Shield (+ family guardian alert)
**Planned modules (6):** Money & Bills · Health · Shopping · Travel · Education & Career · Family Care
**Stack:** React (Vite) · FastAPI · LangGraph multi-agent · MCP server · n8n · SQLite (swap to Postgres with the same schema) · Playwright

## Architecture
```
React UI ──► FastAPI ──► LangGraph:  Router ─► Benefits Agent ─► Safety Agent ─► END
                │                           ├► Scam Shield Agent (+Family Agent) ─► END
                │                           └► Planner Agent (roadmap modules) ─► END
                │            every agent calls tools through ToolBus
                │                 ├── MCP (streamable HTTP) ─► mcp_server/server.py ─► tools.py ─► SQLite
                │                 └── direct fallback if MCP is down
                ├─► Approval gate (DB): nothing consequential runs until the user taps Approve
                ├─► Browser Agent (Playwright) fills + submits the demo gov portal, saves screenshots
                └─► n8n webhooks: application-submitted, scam-alert-guardian; n8n schedule: daily deadline digest
```
Trust features (these answer judge questions): consent-gated vault, approval gate, activity log + undo,
explainable eligibility (shows why you are ruled OUT too), deterministic + explainable scam scoring,
Safety Agent verifies the portal link before the browser opens it, and the whole system works with no LLM key.

## Folder structure
```
lifeagent/
├── backend/app/   main.py (API) · graph.py (LangGraph) · tools.py (all tools) · toolbus.py (MCP/direct)
│                  eligibility.py · scam.py · browser_agent.py · llm.py · modules.py · db.py · seed.py
│                  schema.sql · data/schemes.json · static/portal.html (demo gov portal)
├── mcp_server/    server.py (FastMCP) · claude_desktop_config.example.json
├── n8n/workflows/ 01_application_submitted · 02_daily_deadline_digest · 03_scam_alert_guardian (.json)
├── frontend/src/  App.jsx · screens/{Agent,Benefits,ScamShield,Vault,Activity,Roadmap}.jsx · components/
├── docker-compose.yml · .env.example
```

## Setup (10 minutes)
```bash
# 1. Backend
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt && playwright install chromium
cp ../.env.example ../.env   # then: export $(grep -v '^#' ../.env | sed 's/ *#.*//' | xargs)   (or set vars manually)
uvicorn app.main:app --reload --port 8000

# 2. MCP server (new terminal, same venv)
python mcp_server/server.py          # http://localhost:8001/mcp   (set USE_MCP=1 for the backend to use it)

# 3. n8n (new terminal, repo root)
docker compose up -d                 # open http://localhost:5678, create the owner account
#    Workflows -> Import from file -> import all 3 files in n8n/workflows/ -> toggle each workflow ACTIVE
#    (Webhooks only work on the production URL when the workflow is active.)

# 4. Frontend (new terminal)
cd frontend && npm install && npm run dev     # http://localhost:5173
```
Check: `curl localhost:8000/api/health` -> `{"ok":true,"llm":...,"mcp":...}`. Interactive API docs: `localhost:8000/docs`.

## API summary
| Method | Path | Purpose |
|---|---|---|
| POST | /api/agent/chat | Run the LangGraph agents `{user_id,message}` -> reply, trace, approval |
| GET | /api/schemes/match?user_id= | Eligible + ruled-out schemes with reasons |
| POST | /api/scam/check | Scan text/URL, may queue a guardian alert |
| GET | /api/approvals?user_id= | Pending approvals |
| POST | /api/approvals/{id}/approve \| reject | Execute (browser agent + n8n) or cancel |
| GET/PUT | /api/users/{id}/vault, /consent | Vault view, grant/revoke agent access |
| GET | /api/activity, POST /api/activity/{id}/undo | Audit log and undo |
| GET | /api/deadlines, /api/deadlines/due | Deadlines (n8n polls `/due`) |
| POST | /api/notify | Used by n8n to push notifications into the app |
| GET | /portal | Demo government portal the browser agent operates |

MCP tools: `get_profile, find_schemes, check_message, add_deadline, log_activity, propose_action, record_scam_check`; resource `vault://{user_id}/profile`.

## Live demo script (5 min)
**Prep:** `DEMO_HEADED=1`, USE_MCP=1, n8n workflows active, browser on http://localhost:5173, screen-share a visible Chromium area.
1. **Hook (30s)** Persona *Ravi Kumar (IN, Kannada)*. "Everyday life is a second job. LifeAgent works for you."
2. **Benefits (90s)** Agent tab -> tap "What benefits am I eligible for?" (or mic). Show the trace: Router -> Vault (consent) -> Benefits -> Form -> Safety -> Approval.
   Open the **Benefits** tab to show *why* each scheme matched and why Post-Matric was ruled out. Tap **Approve**: a real Chromium opens, fills the portal field by field, submits, receipt screenshot appears. Open the bell: the **n8n** notification arrived.
3. **Scam Shield (90s)** Scam Shield tab -> Sample 1 -> DANGEROUS 90/100 with reasons. The Family Agent drafts an alert to Ravi's son: Approve -> switch persona to *Arjun Kumar* -> bell shows the guardian alert. Then Sample 3 (real .gov.in link) -> likely safe, so it is not paranoid.
4. **Trust (45s)** Vault tab: switch consent OFF, ask for benefits again: "I need your permission." Activity tab: full log, click **Undo** on a reminder.
5. **International (30s)** Switch to *Maria (US, Spanish)* and *Margaret (UK)*: different schemes from the same engine; new country = new `schemes.json`.
6. **MCP + roadmap (30s)** Say "Same tools are an MCP server, so Claude Desktop or any agent can use LifeAgent" (optional: show Claude Desktop calling `check_message`). Open Roadmap: 6 planned modules plug into the same engine.

**Fallbacks (stay calm):** no LLM key -> rules fallback replies. MCP down -> direct calls. n8n down -> backend fallback notification. Playwright missing -> "simulated" submit. Record a 90-second backup video on day 2.

## Team of 4
| Role | Owns | Day 1 | Day 2 |
|---|---|---|---|
| A. AI/agents lead | graph.py, llm.py, prompts, multilingual replies | Router + Benefits + Scam nodes | Tune prompts, hi/kn/es replies, eval set of 20 scam messages |
| B. Backend/data | main.py, db, tools.py, MCP server, schemes.json | API + MCP + consent | Add 2-3 real schemes per country, tests |
| C. Automation | n8n workflows, browser_agent.py, portal | 3 workflows | Harden browser agent, record backup video |
| D. Frontend/pitch | React screens, demo script, slides | Agent + Scam screens | Polish, voice input, pitch deck, rehearsals |

## Important honesty notes
- `schemes.json` is **illustrative demo data** with simplified rules. Always verify against the official source before real use; say this in the pitch.
- The portal at `/portal` is a **local stand-in** for a government site. Real portals need login/OTP, which the agent hands back to the human (human-fallback principle).
- No real payments or messages are sent anywhere; n8n notifications land inside the app. Add Telegram/Email nodes in n8n to go further.
- Scam scoring is heuristic. Add an LLM second opinion and Google Safe Browsing as the next step.

## Extend (roadmap implementation pattern)
New module = (1) tools in `tools.py` + `@mcp.tool` in `server.py`, (2) one node in `graph.py` + a router label, (3) one screen, (4) optional n8n workflow.
