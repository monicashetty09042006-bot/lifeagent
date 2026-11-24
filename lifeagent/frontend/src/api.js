export async function api(path, opts = {}) {
  const r = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" }, ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
export const post = (p, body) => api(p, { method: "POST", body });
export const put = (p, body) => api(p, { method: "PUT", body });
