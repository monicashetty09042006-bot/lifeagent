import { useState } from "react";
import { post } from "../api";
export default function ApprovalCard({ approval, onDone }) {
  const [busy, setBusy] = useState(false), [res, setRes] = useState(null), [rej, setRej] = useState(false);
  const form = approval.payload?.form;
  const go = async (act) => {
    setBusy(true);
    try { const r = await post(`/approvals/${approval.id}/${act}`); act === "approve" ? setRes(r) : setRej(true); onDone?.(); }
    catch (e) { alert(e.message); } setBusy(false);
  };
  return (
    <div className="card approval">
      <b>Needs your approval:</b> {approval.summary}
      {form && <table><tbody>{Object.entries(form).map(([k, v]) => <tr key={k}><td className="mute">{k}</td><td>{String(v)}</td></tr>)}</tbody></table>}
      {approval.kind === "alert_guardian" && <div className="mute">Will notify your guardian: risk {approval.payload.risk_score}/100.</div>}
      {!res && !rej && <div className="row" style={{ marginTop: 10 }}>
        <button className="btn ok" disabled={busy} onClick={() => go("approve")}>{busy ? "Working…" : "Approve"}</button>
        <button className="btn ghost" disabled={busy} onClick={() => go("reject")}>Reject</button></div>}
      {rej && <div className="mute">Rejected. Nothing was done.</div>}
      {res && <div style={{ marginTop: 10 }}><b className="safe">Done.</b>
        {res.reference && <> Reference <code>{res.reference}</code> ({res.mode} mode)</>}
        {res.n8n !== undefined && <div className="mute">n8n workflow: {res.n8n ? "triggered" : "offline, backend fallback used"}</div>}
        {res.screenshot && <img className="shot" src={res.screenshot} alt="receipt" />}</div>}
    </div>);
}
