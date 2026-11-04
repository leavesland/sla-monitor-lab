"""Tests for worker.py: retries, timeouts, and when alerts are sent.

No real website is contacted. httpx.get is replaced with a fake that plays
back a script of outcomes, like "time out once, then answer 200".
"""

import httpx

from app import alerts, store, worker


def fake_get(script, calls):
    """Return a stand-in for httpx.get that follows `script`, one entry per call."""
    def get(url, **kwargs):
        calls.append(url)
        outcome = script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(outcome)            # outcome is an HTTP status code
    return get


def test_success_does_not_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(worker.httpx, "get", fake_get([200], calls))

    ok, status, _ = worker.check("https://github.com")

    assert (ok, status) == (True, 200)
    assert len(calls) == 1


def test_one_timeout_then_success_counts_as_up(monkeypatch):
    calls = []
    script = [httpx.ConnectTimeout("too slow"), 200]
    monkeypatch.setattr(worker.httpx, "get", fake_get(script, calls))

    ok, status, _ = worker.check("https://github.com")

    assert (ok, status) == (True, 200)
    assert len(calls) == 2                        # the retry saved us from a false alarm


def test_gives_up_after_one_retry(monkeypatch):
    calls = []
    script = [httpx.ConnectTimeout("too slow"), httpx.ConnectTimeout("too slow")]
    monkeypatch.setattr(worker.httpx, "get", fake_get(script, calls))

    ok, status, _ = worker.check("https://nowhere.invalid")

    assert (ok, status) == (False, None)          # no answer at all, so no status code
    assert len(calls) == worker.RETRIES + 1       # 2 tries, then stop


def test_server_error_is_down_but_keeps_the_status(monkeypatch):
    calls = []
    monkeypatch.setattr(worker.httpx, "get", fake_get([500, 500], calls))

    ok, status, _ = worker.check("https://example.com")

    assert (ok, status) == (False, 500)           # it answered, but said "I'm broken"


def test_alert_once_when_down_and_once_when_back_up(fake_redis, monkeypatch):
    store.add_target("GitHub", "https://github.com")
    results = [(False, None, 5000), (False, None, 5000), (True, 200, 210)]
    monkeypatch.setattr(worker, "check", lambda url: results.pop(0))
    sent = []
    monkeypatch.setattr(alerts, "send_alert", sent.append)

    worker.handle("GitHub")      # down: alert
    worker.handle("GitHub")      # still down: no new alert
    worker.handle("GitHub")      # back up: alert

    assert len(sent) == 2
    assert "DOWN" in sent[0]
    assert "back UP" in sent[1]


def test_removed_target_is_skipped(fake_redis, monkeypatch):
    def should_not_be_called(url):
        raise AssertionError("checked a target that was removed")
    monkeypatch.setattr(worker, "check", should_not_be_called)

    worker.handle("Ghost")       # its name was queued, then the target was deleted

    assert store.get_history("Ghost") == []
