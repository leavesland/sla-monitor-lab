"""The API. Compare with simple/main.py: this file does no checking at all.
It only reads and writes Redis. The checking happens in worker.py, in a
different process, possibly on a different machine.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from . import store

DEFAULT_TARGETS = {
    "GitHub": "https://github.com",
    "Example.com": "https://example.com",
    "Slow endpoint": "https://httpbin.org/delay/2",    # answers, but takes 2 s
    "Dead endpoint": "https://nowhere.invalid",        # DNS fails on purpose
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # First boot with an empty Redis: seed something to look at.
    if not store.get_targets():
        for name, url in DEFAULT_TARGETS.items():
            store.add_target(name, url)
    yield


app = FastAPI(title="SLA Monitor API", lifespan=lifespan)


class NewTarget(BaseModel):
    """Shape of the JSON body for POST /api/targets.

    This is the type-hints-validate-input idea from Project 1. If the
    browser sends a missing name or a URL that isn't a URL, FastAPI rejects
    it with a 422 before this code ever runs.
    """
    name: str = Field(min_length=1, max_length=40)
    url: HttpUrl


@app.get("/api/health")
def health():
    return {"status": "ok", "redis": store.ping()}


@app.get("/api/status")
def status():
    out = []
    for name, url in store.get_targets().items():
        results = store.get_history(name)
        latest = results[-1] if results else None
        ups = sum(1 for row in results if row["ok"])
        out.append({
            "name": name,
            "url": url,
            "up": latest["ok"] if latest else None,
            "latency_ms": latest["latency_ms"] if latest else None,
            "status": latest["status"] if latest else None,
            "uptime_pct": round(100 * ups / len(results), 1) if results else None,
            "checks": len(results),
            "history": [row["latency_ms"] if row["ok"] else None for row in results],
        })
    return out


@app.get("/api/incidents")
def incidents():
    return store.get_incidents()


@app.post("/api/targets", status_code=201)
def create_target(body: NewTarget):
    if body.name in store.get_targets():
        raise HTTPException(status_code=409, detail=f"'{body.name}' already exists")
    store.add_target(body.name, str(body.url))
    store.enqueue(body.name)          # check it now instead of waiting for the scheduler
    return {"name": body.name, "url": str(body.url)}


@app.delete("/api/targets/{name}", status_code=204)
def delete_target(name: str):
    if name not in store.get_targets():
        raise HTTPException(status_code=404, detail=f"'{name}' not found")
    store.remove_target(name)
