"""Tests for alerts.py. No real webhook is contacted: httpx.post is faked."""

import httpx

from app import alerts


def test_no_webhook_url_means_alerts_are_off(monkeypatch):
    monkeypatch.setattr(alerts, "WEBHOOK_URL", "")

    def should_not_be_called(*args, **kwargs):
        raise AssertionError("sent a request with alerts turned off")
    monkeypatch.setattr(alerts.httpx, "post", should_not_be_called)

    assert alerts.send_alert("GitHub is DOWN") is False


def test_alert_is_posted_to_the_webhook(monkeypatch):
    monkeypatch.setattr(alerts, "WEBHOOK_URL", "https://example.com/webhook")
    posted = []

    def fake_post(url, json, timeout):
        posted.append((url, json))
        return httpx.Response(204)                # Discord answers 204 No Content
    monkeypatch.setattr(alerts.httpx, "post", fake_post)

    assert alerts.send_alert("GitHub is DOWN") is True
    assert posted == [("https://example.com/webhook", {"content": "GitHub is DOWN"})]


def test_broken_webhook_never_crashes_the_worker(monkeypatch):
    monkeypatch.setattr(alerts, "WEBHOOK_URL", "https://example.com/webhook")

    def broken_post(*args, **kwargs):
        raise httpx.ConnectError("webhook is down")
    monkeypatch.setattr(alerts.httpx, "post", broken_post)

    assert alerts.send_alert("GitHub is DOWN") is False    # no exception escapes
