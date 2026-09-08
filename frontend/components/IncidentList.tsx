import type { Incident } from "@/lib/api";

export default function IncidentList({ incidents }: { incidents: Incident[] }) {
  return (
    <section className="incidents">
      <h2>Incidents</h2>
      {incidents.length === 0 ? (
        <p className="muted">None recorded.</p>
      ) : (
        <ul>
          {incidents.map((inc, i) => (
            <li key={`${inc.target}-${inc.started}-${i}`}>
              <span className={`dot ${inc.ended ? "closed" : "open"}`} />
              <span className="who">{inc.target}</span>
              <span className="what">{inc.ended ? `down for ${duration(inc.started, inc.ended)}` : "down now"}</span>
              <span className="when">{new Date(inc.started).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function duration(startIso: string, endIso: string): string {
  const seconds = Math.round((new Date(endIso).getTime() - new Date(startIso).getTime()) / 1000);
  return seconds < 60 ? `${seconds}s` : `${Math.round(seconds / 60)}m`;
}
