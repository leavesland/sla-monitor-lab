"""Every Redis read and write lives here. Nothing else touches Redis directly.

In the simple version, `history` was a Python dict inside the web server.
Only that one process could see it. Here it lives in Redis, so the API,
the scheduler, and any number of workers all share the same data.

Keys we use:
  targets          hash    name -> url
  jobs             list    the work queue: scheduler LPUSHes names, workers BRPOP them
  history:{name}   list    newest first, one JSON string per check, capped at KEEP_LAST
  state:{name}     string  "up" or "down", the last known state (for incident detection)
  open:{name}      string  ISO timestamp; exists only while the target is currently down
  incidents        list    newest first, closed incidents as JSON
"""

import json
from datetime import datetime, timezone

import redis

from .config import KEEP_LAST, QUEUE_KEY, REDIS_URL

# decode_responses=True means we get Python strings back instead of bytes.
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ping() -> bool:
    return bool(r.ping())


# --- targets -------------------------------------------------------------

def get_targets() -> dict[str, str]:
    return r.hgetall("targets")


def add_target(name: str, url: str) -> None:
    r.hset("targets", name, url)


def remove_target(name: str) -> None:
    r.hdel("targets", name)
    r.delete(f"history:{name}", f"state:{name}", f"open:{name}")


# --- the queue -----------------------------------------------------------

def enqueue(name: str) -> None:
    r.lpush(QUEUE_KEY, name)


def dequeue(timeout: int = 5) -> str | None:
    """Block until a job arrives (or `timeout` seconds pass). Returns the target name."""
    item = r.brpop(QUEUE_KEY, timeout=timeout)
    return item[1] if item else None


def queue_length() -> int:
    return r.llen(QUEUE_KEY)


# --- results and incidents ----------------------------------------------

def record_result(name: str, ok: bool, status: int | None, latency_ms: int) -> None:
    """Save one check and update incident state."""
    r.lpush(f"history:{name}", json.dumps({
        "at": now(), "ok": ok, "status": status, "latency_ms": latency_ms,
    }))
    r.ltrim(f"history:{name}", 0, KEEP_LAST - 1)     # keep only the newest KEEP_LAST

    previous = r.get(f"state:{name}")                # None on the very first check
    current = "up" if ok else "down"

    if current == "down" and previous != "down":
        # Just went down (or has been down since the first check): open an incident.
        r.set(f"open:{name}", now())
    elif current == "up" and previous == "down":
        # Just recovered: close the open incident and file it.
        started = r.get(f"open:{name}")
        if started:
            r.lpush("incidents", json.dumps({"target": name, "started": started, "ended": now()}))
            r.ltrim("incidents", 0, 99)
        r.delete(f"open:{name}")

    r.set(f"state:{name}", current)


def get_history(name: str) -> list[dict]:
    rows = [json.loads(x) for x in r.lrange(f"history:{name}", 0, -1)]
    return rows[::-1]                                # oldest first, so charts read left to right


def get_incidents() -> list[dict]:
    open_now = []
    for name in get_targets():
        started = r.get(f"open:{name}")
        if started:
            open_now.append({"target": name, "started": started, "ended": None})
    closed = [json.loads(x) for x in r.lrange("incidents", 0, 19)]
    return open_now + closed
