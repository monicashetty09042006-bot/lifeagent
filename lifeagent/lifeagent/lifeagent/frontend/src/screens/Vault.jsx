import { useEffect, useState } from "react";
import { api, put } from "../api";
export default function Vault({ user }) {
  const [v, setV] = useState(null);
  const load = () => api(`/users/${user.id}/vault`).then(setV);
  useEffect(() => { load(); }, [user.id]);
  if (!v) return <div className="mute">Loading…</div>;
  const p = v.profile;
  return (<div>
    <div className="card row"><div className="grow"><b>Vault access for LifeAgent</b>
      <div className="mute">Agents can read your vault only while this is on. Try turning it off and asking for benefits.</div></div>
      <button className={"btn " + (v.consent ? "ok" : "bad")} onClick={async () => { await put(`/users/${user.id}/consent`, { granted: !v.consent }); load(); }}>{v.consent ? "ON" : "OFF"}</button></div>
    <div className="card"><b>Profile</b><table><tbody>{["name", "country", "language", "age", "gender", "occupation", "annual_income", "currency", "household_size"].map((k) => <tr key={k}><td className="mute">{k}</td><td>{String(p[k])}</td></tr>)}</tbody></table></div>
    <div className="card"><b>Documents</b>{v.documents.map((d) => <div key={d.id}>📄 {d.title} <span className="mute">({d.doc_type})</span></div>)}</div>
  </div>);
}
