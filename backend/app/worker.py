"""A worker. Pulls one job off the queue, checks that URL, records the result,
repeats forever. Run one of these or run ten; they share the queue.

This is where "concurrent checks with timeouts and retries" actually lives:
  - concurrency comes from running several workers, not from clever code
  - the timeout means one hanging target costs one worker at most
    TIMEOUT_SECONDS * (RETRIES + 1) seconds, while the others keep going
"""

import os
import time

import httpx

from . import store
from .config import RETRIES, TIMEOUT_SECONDS

# Docker sets HOSTNAME to the container id, so each worker gets a distinct label.
WORKER_ID = os.getenv("HOSTNAME", "local")[:12]


def check(url: str) -> tuple[bool, int | None, int]:
    """Fetch the URL, retrying on failure. Returns (ok, http_status, latency_ms)."""
    ok, status, latency_ms = False, None, 0
    for _attempt in range(RETRIES + 1):
        started = time.perf_counter()
        try:
            response = httpx.get(url, timeout=TIMEOUT_SECONDS, follow_redirects=True)
            status = response.status_code
            ok = 200 <= status < 400
        except httpx.HTTPError:          # timeout, DNS failure, connection refused, ...
            status, ok = None, False
        latency_ms = round((time.perf_counter() - started) * 1000)
        if ok:
            break
    return ok, status, latency_ms


def main() -> None:
    print(f"worker {WORKER_ID}: started", flush=True)
    while True:
        name = store.dequeue(timeout=5)
        if name is None:
            continue                                 # queue was empty; go back to waiting

        url = store.get_targets().get(name)
        if url is None:
            continue                                 # target was removed after being queued

        ok, status, latency_ms = check(url)
        store.record_result(name, ok, status, latency_ms)
        print(f"worker {WORKER_ID}: {name:14} {'UP  ' if ok else 'DOWN'}  status={status}  {latency_ms} ms", flush=True)


if __name__ == "__main__":
    main()
