"""Shared test setup.

fakeredis is a fake Redis that lives in memory. Swapping it in for the real
connection means most tests need no Redis server, and every test starts
with a clean, empty "Redis".
"""

import fakeredis
import pytest

from app import store


@pytest.fixture
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(store, "r", fake)    # store.py now talks to the fake
    return fake
