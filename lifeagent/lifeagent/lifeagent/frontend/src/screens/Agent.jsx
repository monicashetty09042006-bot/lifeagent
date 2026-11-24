import { useState, useRef } from "react";
import { post } from "../api";
import TraceView from "../components/TraceView";
import ApprovalCard from "../components/ApprovalCard";
const LANG = { en: "en-US", hi: "hi-IN", kn: "kn-IN", es: "es-ES" };
const CHIPS = ["What benefits am I eligible for?",
  "Is this safe? Dear customer your SBI account will be blocked today. Verify KYC at http://sbi-kyc-update.xyz/login and share OTP",
  "Help me with my medical bills", "Plan a trip to Goa"];
export default function Agent({ user }) {
  const [msgs, setMsgs] = useState([]), [text, setText] = useState(""), [busy, setBusy] = useState(false), rec = useRef(null);
  const send = async (m) => {
    const t = (m ?? text).trim(); if (!t) return;
    setText(""); setBusy(true); setMsgs((x) => [...x, { role: "u", text: t }]);
    try { const r = await post("/agent/chat", { user_id: user.id, message: t }); setMsgs((x) => [...x, { role: "a", ...r }]); }
    catch (e) { setMsgs((x) => [...x, { role: "a", reply: "Error: " + e.message }]); }
    setBusy(false);
  };
  const mic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice input needs Chrome or Edge.");
    const r = new SR(); r.lang = LANG[user.language] || "en-US";
    r.onresult = (e) => send(e.results[0][0].transcript); r.start(); rec.current = r;
  };
  return (<div>
    <div className="card"><div className="mute">Tell it your goal. It does the work, and you stay in control.</div>
      <div className="row" style={{ marginTop: 8 }}>{CHIPS.map((c) => <span key={c} className="chip" onClick={() => send(c)}>{c.length > 48 ? c.slice(0, 48) + "…" : c}</span>)}</div></div>
    <div className="chat">{msgs.map((m, i) => m.role === "u" ? <div key={i} className="msg u">{m.text}</div> :
      <div key={i} className="msg a">{m.reply}<TraceView trace={m.trace} />
        {m.approval && <ApprovalCard approval={m.approval} />}</div>)}
      {busy && <div className="mute">Agents are working…</div>}</div>
    <div className="row" style={{ marginTop: 14 }}>
      <input className="grow" value={text} placeholder="Type or tap the mic…" onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
      <button className="btn ghost" onClick={mic} title="Voice">🎤</button>
      <button className="btn" disabled={busy} onClick={() => send()}>Send</button></div></div>);
}
