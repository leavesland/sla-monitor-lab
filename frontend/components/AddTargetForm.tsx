"use client";

import { useState, type FormEvent } from "react";
import { addTarget } from "@/lib/api";

export default function AddTargetForm({ onAdded }: { onAdded: () => void }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();               // stop the browser from reloading the page
    setBusy(true);
    setError("");
    try {
      await addTarget(name.trim(), url.trim());
      setName("");
      setUrl("");
      onAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add target");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="add" onSubmit={submit}>
      <h2>Watch a new URL</h2>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" maxLength={40} required />
      <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" type="url" required />
      <button type="submit" disabled={busy}>{busy ? "Adding…" : "Add target"}</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
