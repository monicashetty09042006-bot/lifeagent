import { useState } from "react";
import { post } from "../api";
import ApprovalCard from "../components/ApprovalCard";
const SAMPLES = ["Dear customer your SBI account will be blocked today. Verify KYC at http://sbi-kyc-update.xyz/login and share OTP",
  "Your parcel is held. Pay a processing fee at paypa1.com/pay or bit.ly/3xYz immediately",
  "Apply for PM-KISAN at https://pmkisan.gov.in", "Hi, are we still on for lunch tomorrow?"];
export default function ScamShield({ user }) {
  const [text, setText] = useState(""), [out, setOut] = useState(null), [busy, setBusy] = useState(false);
  const scan = async () => { setBusy(true); setOut(await post("/scam/check", { user_id: user.id, text })); setBusy(false); };
  const r = out?.result, cls = r && (r.verdict === "dangerous" ? "dangerous" : r.verdict === "suspicious" ? "suspicious" : "safe");
  const color = r && (r.risk_score >= 70 ? "var(--bad)" : r.risk_score >= 40 ? "var(--warn)" : "var(--ok)");
  return (<div>
    <div className="card"><b>Paste a message, link or email before you act on it.</b>
      <textarea style={{ width: "100%", marginTop: 8 }} rows={4} value={text} onChange={(e) => setText(e.target.value)} />
      <div className="row" style={{ marginTop: 8 }}>{SAMPLES.map((s, i) => <span key={i} className="chip" onClick={() => setText(s)}>Sample {i + 1}</span>)}
        <span className="grow" /><button className="btn" disabled={busy || !text} onClick={scan}>{busy ? "Checking…" : "Check"}</button></div></div>
    {r && <div className="card"><h3 className={cls} style={{ margin: 0 }}>{r.verdict.toUpperCase()} · {r.risk_score}/100</h3>
      <div className="gauge" style={{ margin: "8px 0" }}><i style={{ width: r.risk_score + "%", background: color }} /></div>
      <p>{out.reply}</p><ul>{r.reasons.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
    {out?.approval && <ApprovalCard approval={out.approval} />}
  </div>);
}
