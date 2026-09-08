import Sparkline from "./Sparkline";
import type { TargetStatus } from "@/lib/api";

type Props = {
  target: TargetStatus;
  onRemove: (name: string) => void;
};

export default function TargetCard({ target: t, onRemove }: Props) {
  const state = t.up === null ? "wait" : t.up ? "up" : "down";
  const label = t.up === null ? "WAITING" : t.up ? "UP" : "DOWN";

  return (
    <article className="card">
      <div className="top">
        <div>
          <div className="name">{t.name}</div>
          <div className="url">{t.url}</div>
        </div>
        <div className="right">
          <span className={`pill ${state}`}>{label}</span>
          <button className="remove" onClick={() => onRemove(t.name)} aria-label={`Remove ${t.name}`} title="Remove">
            ×
          </button>
        </div>
      </div>
      <div className="stats">
        <Stat value={t.latency_ms} unit="ms" />
        <Stat value={t.uptime_pct === null ? null : `${t.uptime_pct}%`} unit="uptime" />
        <Stat value={t.status} unit="status" />
        <Stat value={t.checks} unit="checks" />
      </div>
      <Sparkline history={t.history} />
    </article>
  );
}

function Stat({ value, unit }: { value: number | string | null; unit: string }) {
  return (
    <div className="stat">
      <b>{value ?? "–"}</b>
      <span>{unit}</span>
    </div>
  );
}
