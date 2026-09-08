// The one place the frontend talks to the backend.
//
// The two `type`s below are the reason for TypeScript in this project. They
// describe exactly what /api/status and /api/incidents return. Get a field
// name wrong anywhere in a component and the build fails, instead of the
// page silently showing "undefined".

export type TargetStatus = {
  name: string;
  url: string;
  up: boolean | null;            // null until the first check has run
  latency_ms: number | null;
  status: number | null;         // HTTP status; null when the request itself failed
  uptime_pct: number | null;
  checks: number;
  history: (number | null)[];    // latency per check, null where the check failed
};

export type Incident = {
  target: string;
  started: string;               // ISO timestamp
  ended: string | null;          // null while still down
};

async function fail(res: Response): Promise<never> {
  let message = `${res.status} ${res.statusText}`;
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail)) message = detail.map((d: { msg: string }) => d.msg).join("; ");
  } catch {
    // body wasn't JSON; keep the status text
  }
  throw new Error(message);
}

export async function fetchStatus(): Promise<TargetStatus[]> {
  const res = await fetch("/api/status", { cache: "no-store" });
  if (!res.ok) return fail(res);
  return res.json();
}

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch("/api/incidents", { cache: "no-store" });
  if (!res.ok) return fail(res);
  return res.json();
}

export async function addTarget(name: string, url: string): Promise<void> {
  const res = await fetch("/api/targets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url }),
  });
  if (!res.ok) return fail(res);
}

export async function removeTarget(name: string): Promise<void> {
  const res = await fetch(`/api/targets/${encodeURIComponent(name)}`, { method: "DELETE" });
  if (!res.ok) return fail(res);
}
