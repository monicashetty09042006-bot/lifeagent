import { useEffect, useState } from "react";
import { api, post } from "../api";
export default function Activity({ user }) {
  const [rows, setRows] = useState([]), [dl, setDl] = useState([]);
  const load = () => { api(`/activity?user_id=${user.id}`).then(setRows); api(`/deadlines?user_id=${user.id}`).then(setDl); };
  useEffect(() => { load(); const t = setInterval(load, 4000); return () => clearInterval(t); }, [user.id]);
  return (<div>
    <div className="card"><b>Upcoming deadlines</b>{dl.length === 0 && <div className="mute">None.</div>}{dl.map((d) => <div key={d.id}>⏰ {d.due_date} — {d.title}</div>)}</div>
    <div className="card"><b>Everything the agents did</b><table><tbody>{rows.map((a) => <tr key={a.id}>
      <td className="mute">{a.created_at?.slice(5, 16)}</td><td><b>{a.agent}</b></td><td>{a.action}<div className="mute">{a.detail}</div></td><td>{a.status}</td>
      <td>{a.undoable && a.status === "done" ? <button className="btn ghost" onClick={async () => { await post(`/activity/${a.id}/undo`); load(); }}>Undo</button> : null}</td></tr>)}</tbody></table></div></div>);
}
