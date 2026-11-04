"""Settings. Every value can be overridden with an environment variable,
which is how docker-compose.yml points the services at the shared Redis."""

import os

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

CHECK_EVERY_SECONDS = int(os.getenv("CHECK_EVERY_SECONDS", "10"))
TIMEOUT_SECONDS = float(os.getenv("TIMEOUT_SECONDS", "5"))
RETRIES = int(os.getenv("RETRIES", "1"))          # extra attempts after the first failure
KEEP_LAST = int(os.getenv("KEEP_LAST", "60"))     # results per target kept in Redis

# Where to send alerts when an incident opens or closes, for example a
# Discord channel webhook. Empty means alerts are off.
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

QUEUE_KEY = "jobs"
