"""Tests for store.py: incidents, history, the queue, and cleanup."""

from app import store
from app.config import KEEP_LAST


def test_incident_opens_once_and_closes_on_recovery(fake_redis):
    store.add_target("GitHub", "https://github.com")

    assert store.record_result("GitHub", ok=True, status=200, latency_ms=200) is None
    assert store.get_incidents() == []

    # Goes down: one incident opens.
    assert store.record_result("GitHub", ok=False, status=None, latency_ms=5000) == "opened"
    incidents = store.get_incidents()
    assert len(incidents) == 1
    assert incidents[0]["ended"] is None

    # Still down: no second incident.
    assert store.record_result("GitHub", ok=False, status=None, latency_ms=5000) is None
    assert len(store.get_incidents()) == 1

    # Comes back: the incident closes and is filed.
    assert store.record_result("GitHub", ok=True, status=200, latency_ms=210) == "closed"
    incidents = store.get_incidents()
    assert len(incidents) == 1
    assert incidents[0]["target"] == "GitHub"
    assert incidents[0]["ended"] is not None


def test_first_check_down_opens_an_incident(fake_redis):
    store.add_target("Dead endpoint", "https://nowhere.invalid")

    assert store.record_result("Dead endpoint", ok=False, status=None, latency_ms=12) == "opened"
    assert store.get_incidents()[0]["ended"] is None


def test_history_keeps_only_the_newest_results_oldest_first(fake_redis):
    for latency in range(KEEP_LAST + 5):                 # 65 checks: latency 0, 1, ..., 64
        store.record_result("GitHub", ok=True, status=200, latency_ms=latency)

    history = store.get_history("GitHub")
    assert len(history) == KEEP_LAST                     # only 60 kept
    assert history[0]["latency_ms"] == 5                 # 0 to 4 were dropped
    assert history[-1]["latency_ms"] == KEEP_LAST + 4    # newest is last, for the chart


def test_queue_is_first_in_first_out(fake_redis):
    store.enqueue("GitHub")
    store.enqueue("Example.com")

    assert store.dequeue(timeout=1) == "GitHub"
    assert store.dequeue(timeout=1) == "Example.com"
    assert store.dequeue(timeout=1) is None              # empty queue: None, not a crash


def test_removing_a_target_cleans_up_its_data(fake_redis):
    store.add_target("GitHub", "https://github.com")
    store.record_result("GitHub", ok=False, status=None, latency_ms=5000)

    store.remove_target("GitHub")

    assert "GitHub" not in store.get_targets()
    assert store.get_history("GitHub") == []
    assert store.get_incidents() == []
