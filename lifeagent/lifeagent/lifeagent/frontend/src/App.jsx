import { useEffect, useState } from "react";
import { api } from "./api";
import Agent from "./screens/Agent"; import Benefits from "./screens/Benefits"; import ScamShield from "./screens/ScamShield";
import Vault from "./screens/Vault"; import Activity from "./screens/Activity"; import Roadmap from "./screens/Roadmap";
const TABS = [["agent", "Agent"], ["benefits", "Benefits"], ["scam", "Scam Shield"], ["vault", "Vault"], ["activity", "Activity & Undo"], ["roadmap", "Roadmap"]];
export default function App() {
  const [users, setUsers] = useState([]), [uid, setUid] = useState(1), [tab, setTab] = useState("agent"), [notes, setNotes] = useState([]), [open, setOpen] = useState(false);
  useEffect(() => { api("/users").then(setUsers); }, []);
  useEffect(() => { const f = () => api(`/notifications?user_id=${uid}`).then(setNotes).catch(() => {}); f(); const t = setInterval(f, 3000); return () => clearInterval(t); }, [uid]);
  const user = users.find((u) => u.id === uid);
  if (!user) return <div style={{ padding: 20 }}>Connecting to LifeAgent API…</div>;
  const S = { agent: Agent, benefits: Benefits, scam: ScamShield, vault: Vault, activity: Activity, roadmap: Roadmap }[tab];
  return (<>
    <header><h1>LifeAgent<small>one agent for your whole day</small></h1>
      <select value={uid} onChange={(e) => setUid(+e.target.value)}>{users.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.country}, {u.language})</option>)}</select>
      <button className="btn ghost" onClick={() => setOpen(!open)}>🔔 {notes.length}</button></header>
    {open && <div className="card" style={{ margin: 12 }}><b>Notifications (via n8n)</b>{notes.length === 0 && <div className="mute">Nothing yet.</div>}
      {notes.map((n) => <div key={n.id}><b>{n.title}</b> <span className="mute">[{n.channel}]</span><div className="mute">{n.body}</div></div>)}</div>}
    <nav>{TABS.map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}</nav>
    <main><S key={uid + tab} user={user} /></main></>);
}
