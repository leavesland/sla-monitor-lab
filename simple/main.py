"""
SLA Monitor, the smallest version that actually works.

Every few seconds, ping each URL in TARGETS, remember what happened,
and serve a page that shows it. Results live in memory: restart the
server and the history is gone. That is what a database would fix.
"""

import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse

# ---------------------------------------------------------------------
# What to watch. Name -> URL. Edit this list and restart.
# ---------------------------------------------------------------------

TARGETS = {
    "GitHub": "https://github.com",
    "Example.com": "https://example.com",
    "Slow endpoint": "https://httpbin.org/delay/2",       # answers, but takes 2 s
    "Dead endpoint": "https://nowhere.invalid",           # DNS fails on purpose
}

CHECK_EVERY_SECONDS = 10   # how often the loop runs
TIMEOUT_SECONDS = 5        # give up on a target after this long
KEEP_LAST = 60             # results per target held in memory

# ---------------------------------------------------------------------
# Where results live. A deque with maxlen drops the oldest automatically.
# ---------------------------------------------------------------------

history: dict[str, deque] = {name: deque(maxlen=KEEP_LAST) for name in TARGETS}


async def check_one(client: httpx.AsyncClient, name: str, url: str) -> None:
    """Ping one URL once and record the result."""
    started = time.perf_counter()
    try:
        response = await client.get(url, timeout=TIMEOUT_SECONDS)
        status = response.status_code
        ok = 200 <= status < 400
    except httpx.HTTPError:            # timeout, DNS failure, refused, etc.
        status = None
        ok = False
    latency_ms = round((time.perf_counter() - started) * 1000)

    history[name].append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": ok,
        "status": status,
        "latency_ms": latency_ms,
    })
    print(f"{name:14} {'UP  ' if ok else 'DOWN'}  status={status}  {latency_ms} ms")


async def checker_loop() -> None:
    """Runs forever in the background: check every target, wait, repeat."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            # gather() fires all checks at once instead of one after another,
            # so a slow target does not delay the others.
            await asyncio.gather(
                *(check_one(client, name, url) for name, url in TARGETS.items())
            )
            await asyncio.sleep(CHECK_EVERY_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the checker when the server starts, stop it when the server stops."""
    task = asyncio.create_task(checker_loop())
    yield
    task.cancel()


app = FastAPI(title="SLA Monitor", lifespan=lifespan)


@app.get("/")
def page():
    """The dashboard. Just hands the browser index.html."""
    return FileResponse("index.html")


@app.get("/api/status")
def status():
    """Everything the page needs, as JSON. One entry per target."""
    out = []
    for name, url in TARGETS.items():
        results = list(history[name])
        latest = results[-1] if results else None
        ups = sum(1 for r in results if r["ok"])
        out.append({
            "name": name,
            "url": url,
            "up": latest["ok"] if latest else None,
            "latency_ms": latest["latency_ms"] if latest else None,
            "status": latest["status"] if latest else None,
            "uptime_pct": round(100 * ups / len(results), 1) if results else None,
            "checks": len(results),
            # latency per check; None where the check failed
            "history": [r["latency_ms"] if r["ok"] else None for r in results],
        })
    return out
