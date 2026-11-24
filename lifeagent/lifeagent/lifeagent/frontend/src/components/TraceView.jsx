export default function TraceView({ trace }) {
  if (!trace?.length) return null;
  return (<div className="trace"><div className="mute">Agent trace (what happened, step by step)</div>
    {trace.map((t, i) => <div key={i}><b>{t.agent}</b> · <code>{t.tool}</code> — {t.summary}</div>)}</div>);
}
