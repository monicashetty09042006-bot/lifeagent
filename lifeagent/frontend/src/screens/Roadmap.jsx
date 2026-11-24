import { useEffect, useState } from "react";
import { api } from "../api";
export default function Roadmap() {
  const [m, setM] = useState(null);
  useEffect(() => { api("/modules").then(setM); }, []);
  if (!m) return null;
  return (<div><p className="mute">One engine (vault, agentic browser, approval gate, activity log, MCP tools). New life areas plug in as new agents.</p>
    <div className="grid">{[...m.live, ...m.planned].map((x) => <div className="card" key={x.id}>
      <div className="row"><b className="grow">{x.name}</b><span className={"badge " + x.status}>{x.status}</span></div>
      <div className="mute">{x.plan || "Working in this prototype."}</div></div>)}</div></div>);
}
