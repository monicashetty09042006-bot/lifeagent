import { useEffect, useState } from "react";
import { api, post } from "../api";
import ApprovalCard from "../components/ApprovalCard";
export default function Benefits({ user }) {
  const [m, setM] = useState(null), [apps, setApps] = useState([]), [ap, setAp] = useState(null);
  const load = () => { api(`/schemes/match?user_id=${user.id}`).then(setM); api(`/applications?user_id=${user.id}`).then(setApps); };
  useEffect(load, [user.id]);
  const prepare = async () => { const r = await post("/agent/chat", { user_id: user.id, message: "What benefits am I eligible for?" }); setAp(r.approval); };
  if (!m) return <div className="mute">Loading…</div>;
  if (m.error) return <div className="card">Vault access is off. Enable it in the Vault tab.</div>;
  return (<div>
    <div className="row"><h3 className="grow">You qualify for {m.eligible.length}</h3><button className="btn" onClick={prepare}>Prepare top application</button></div>
    {ap && <ApprovalCard approval={ap} onDone={load} />}
    <div className="grid">{m.eligible.map((s) => <div className="card" key={s.id}><b>{s.name}</b><div>{s.benefit}</div>
      <div className="mute">{s.authority} · deadline {s.deadline}</div>
      <ul>{s.reasons.map((r, i) => <li key={i} className="safe" style={{ fontSize: 13 }}>✓ {r}</li>)}</ul></div>)}</div>
    {m.not_eligible.length > 0 && <><h4>Ruled out (and why)</h4>{m.not_eligible.map((s) => <div className="card" key={s.id}>{s.name}<div className="mute">{s.failed.join("; ")}</div></div>)}</>}
    <h4>Submitted applications</h4>
    {apps.length === 0 ? <div className="mute">None yet.</div> : <div className="card"><table><tbody>{apps.map((a) => <tr key={a.id}><td>{a.scheme_name}</td><td><code>{a.reference}</code></td><td>{a.status}</td><td className="mute">{a.mode}</td></tr>)}</tbody></table></div>}
  </div>);
}
