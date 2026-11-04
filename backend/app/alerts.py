"""Webhook alerts. When an incident opens or closes, POST a short message to
WEBHOOK_URL, for example a Discord channel webhook.

Two rules:
  - Alert on a change (up -> down, down -> up), not on every failed check,
    so a dead site doesn't send a message every 10 seconds.
  - A broken webhook must never crash the worker. Monitoring keeps going
    even if the alert can't be delivered.
"""

import httpx

from .config import WEBHOOK_URL


def send_alert(message: str) -> bool:
    """Send one message. Returns True if the webhook accepted it."""
    if not WEBHOOK_URL:
        return False                     # alerts are turned off
    try:
        response = httpx.post(WEBHOOK_URL, json={"content": message}, timeout=5)
        return response.is_success
    except httpx.HTTPError:              # timeout, DNS failure, connection refused, ...
        return False
