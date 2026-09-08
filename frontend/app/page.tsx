"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchIncidents, fetchStatus, removeTarget,
  type Incident, type TargetStatus,
} from "@/lib/api";
import TargetCard from "@/components/TargetCard";
import AddTargetForm from "@/components/AddTargetForm";
import IncidentList from "@/components/IncidentList";

const POLL_MS = 5000;

export default function Page() {
  // React state: when any of these change, React redraws the parts that use them.
  const [targets, setTargets] = useState<TargetStatus[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [updatedAt, setUpdatedAt] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [t, i] = await Promise.all([fetchStatus(), fetchIncidents()]);
      setTargets(t);
      setIncidents(i);
      setUpdatedAt(new Date().toLocaleTimeString());
      setError("");
    } catch {
      setError("API unreachable");
    }
  }, []);

  // Same idea as setInterval in simple/index.html, wrapped so React starts it
  // when the page mounts and stops it when the page goes away.
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  async function handleRemove(name: string) {
    await removeTarget(name);
    refresh();
  }

  return (
    <>
      <header>
        <h1>SLA Monitor</h1>
        <div className="meta">{error || (updatedAt ? `updated ${updatedAt}` : "waiting for first check…")}</div>
      </header>
      <main>
        <section className="grid">
          {targets.map((t) => (
            <TargetCard key={t.name} target={t} onRemove={handleRemove} />
          ))}
        </section>
        <aside className="side">
          <AddTargetForm onAdded={refresh} />
          <IncidentList incidents={incidents} />
        </aside>
      </main>
    </>
  );
}
