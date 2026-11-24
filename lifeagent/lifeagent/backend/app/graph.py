"""LangGraph multi-agent orchestration:
router -> (benefits -> safety) | scam | planned -> END"""
import datetime as dt
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from . import llm
from .modules import match_module, PLANNED
from .toolbus import call

SYS = ("You are LifeAgent, a warm assistant that explains things in plain words. "
       "Never claim an action is done before the user approves it. Be concise.")

class State(TypedDict, total=False):
    user_id: int; message: str; language: str; intent: str
    trace: List[dict]; reply: str; approval: Optional[dict]; result: Optional[dict]

def step(s, agent, tool, summary):
    s["trace"].append({"agent": agent, "tool": tool, "summary": summary})

SCAM_KW = ("http", "www.", "otp", "scam", "suspicious", "fraud", "phish", "lottery", "prize", "click", "kyc", ".com", ".xyz")
BEN_KW = ("scheme", "benefit", "subsid", "eligib", "scholar", "apply", "refund", "pension", "grant", "qualif", "welfare", "aid", "eligible")

async def router(s: State):
    m = s["message"].lower()
    out = await llm.complete("Classify a life-admin request. Reply with exactly one word: benefits, scam, or planned.", s["message"], 5)
    intent = out.strip().lower() if out and out.strip().lower() in ("benefits", "scam", "planned") else None
    if not intent:
        intent = "scam" if any(k in m for k in SCAM_KW) else "benefits" if any(k in m for k in BEN_KW) else "planned"
    step(s, "Router Agent", "classify", f"Intent = {intent}" + (" (LLM)" if out else " (rules)"))
    return {"intent": intent, "trace": s["trace"]}

async def benefits_agent(s: State):
    uid = s["user_id"]
    prof = await call("get_profile", user_id=uid)
    if prof.get("error"):
        step(s, "Vault Agent", "get_profile", "Blocked: you have not granted vault access")
        return {"reply": "I need your permission to read your vault before I can look for benefits. Turn on 'Vault access' in the Vault tab.", "trace": s["trace"]}
    step(s, "Vault Agent", "get_profile", f"Read profile with consent: {prof['country']}, age {prof['age']}, {prof['occupation']}, {len(prof['documents'])} documents")
    m = await call("find_schemes", user_id=uid)
    el = m["eligible"]
    step(s, "Benefits Agent", "find_schemes", f"{len(el)} eligible, {len(m['not_eligible'])} ruled out (with reasons)")
    if not el:
        return {"reply": "I checked the schemes I know for your country and none match right now. I will keep watching.", "result": m, "trace": s["trace"]}
    top = el[0]
    form = {"full_name": prof["name"], "age": prof["age"], "country": prof["country"], "occupation": prof["occupation"],
            "annual_income": prof["annual_income"], "household_size": prof["household_size"],
            "id_number": next((d["content"].get("number", "") for d in prof["documents"] if d["doc_type"] == "id_proof"), "")}
    step(s, "Form Agent", "prefill", f"Prepared the {top['name']} form from your vault ({len(form)} fields)")
    ap = await call("propose_action", user_id=uid, kind="apply_scheme", summary=f"Apply to {top['name']}",
                    payload={"scheme": top, "form": form})
    lst = "\n".join(f"- {e['name']} ({e['benefit']}), deadline {e['deadline']}" for e in el)
    txt = await llm.complete(SYS, f"Reply in language code '{s['language']}'. Max 90 words. User eligible for:\n{lst}\n"
                                  f"Recommend the first, say the application is prepared and waits for their approval.")
    reply = txt or (f"You qualify for {len(el)} scheme(s):\n{lst}\n\nI prepared the {top['name']} application from your vault. "
                    f"Review it below and approve when ready.")
    return {"reply": reply, "approval": ap, "result": m, "trace": s["trace"]}

async def safety_agent(s: State):
    if not s.get("approval"):
        return {"trace": s["trace"]}
    url = s["approval"]["payload"]["scheme"]["url"]
    r = await call("check_message", text=url)
    step(s, "Safety Agent", "check_message", f"Verified portal {url}: risk {r['risk_score']}/100 ({r['verdict']})")
    return {"trace": s["trace"]}

async def scan_message(uid: int, text: str, trace: list, language: str = "en"):
    """Shared by the chat agent and the Scam Shield screen."""
    r = await call("check_message", text=text)
    trace.append({"agent": "Scam Shield Agent", "tool": "check_message", "summary": f"Risk {r['risk_score']}/100: {r['verdict']}"})
    await call("record_scam_check", user_id=uid, text=text, result=r)
    ap = None
    prof = await call("get_profile", user_id=uid)
    gid = prof.get("guardian_user_id") if not prof.get("error") else None
    if r["risk_score"] >= 70 and gid:
        ap = await call("propose_action", user_id=uid, kind="alert_guardian", summary="Warn your family guardian about this scam",
                        payload={"guardian_id": gid, "risk_score": r["risk_score"], "reasons": r["reasons"][:3]})
        trace.append({"agent": "Family Agent", "tool": "propose_action", "summary": "Drafted a guardian alert; waiting for your approval"})
    txt = await llm.complete(SYS, f"Reply in language code '{language}'. Max 70 words. Explain to a non-technical person why this message is "
                                  f"{r['verdict']} (score {r['risk_score']}). Findings: {r['reasons']}. Tell them what to do.")
    reply = txt or f"Verdict: {r['verdict'].upper()} ({r['risk_score']}/100). " + " ".join(r["advice"])
    return r, ap, reply

async def scam_agent(s: State):
    r, ap, reply = await scan_message(s["user_id"], s["message"], s["trace"], s["language"])
    return {"reply": reply, "result": r, "approval": ap, "trace": s["trace"]}

async def planned_agent(s: State):
    mod = match_module(s["message"])
    if mod:
        step(s, "Planner Agent", "roadmap", f"'{mod['name']}' module is on the roadmap")
        return {"reply": f"{mod['name']} is coming next. {mod['plan']} Today I can find benefits you qualify for and check suspicious messages.", "trace": s["trace"]}
    step(s, "Planner Agent", "roadmap", "No module matched")
    return {"reply": "Right now I can (1) find government benefits you qualify for and (2) check suspicious links or messages. More life areas are on the roadmap.", "trace": s["trace"]}

g = StateGraph(State)
g.add_node("router", router); g.add_node("benefits", benefits_agent); g.add_node("safety", safety_agent)
g.add_node("scam", scam_agent); g.add_node("planned", planned_agent)
g.set_entry_point("router")
g.add_conditional_edges("router", lambda s: s["intent"], {"benefits": "benefits", "scam": "scam", "planned": "planned"})
g.add_edge("benefits", "safety"); g.add_edge("safety", END); g.add_edge("scam", END); g.add_edge("planned", END)
graph = g.compile()
