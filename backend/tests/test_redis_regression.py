"""Regression test for a real bug, run against a real Redis server.

The bug: the redis library gives up reading after 5 seconds by default, and
dequeue() also waits 5 seconds for a job. So whenever the queue was empty,
both timers ran out together and the worker crashed with a TimeoutError.
Docker restarted it every time, which hid the problem.

fakeredis can't reproduce a network timeout, so this test needs a real
Redis. GitHub Actions starts one. On your laptop it is skipped unless a
Redis server is reachable at REDIS_URL.
"""

import pytest
import redis

from app import store
from app.config import QUEUE_KEY


def real_redis_is_running() -> bool:
    try:
        return bool(store.r.ping())
    except redis.exceptions.RedisError:
        return False


@pytest.mark.skipif(not real_redis_is_running(), reason="needs a real Redis server")
def test_waiting_on_an_empty_queue_returns_none_instead_of_crashing():
    store.r.delete(QUEUE_KEY)
    assert store.dequeue(timeout=5) is None       # used to raise TimeoutError
