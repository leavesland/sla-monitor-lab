"""The scheduler. One tiny process with one job:
every CHECK_EVERY_SECONDS, put every target's name on the queue.

It never pings anything itself. Workers do that. Separating "decide what
to check" from "actually check it" is what lets you run one scheduler and
as many workers as you want.
"""

import time

from . import store
from .config import CHECK_EVERY_SECONDS


def main() -> None:
    print("scheduler: started", flush=True)
    while True:
        names = list(store.get_targets())
        backlog = store.queue_length()

        if backlog > 5 * max(len(names), 1):
            # Nobody is draining the queue. Don't make it worse.
            print(f"scheduler: backlog is {backlog}, skipping this round. Are workers running?", flush=True)
        else:
            for name in names:
                store.enqueue(name)
            print(f"scheduler: queued {len(names)} jobs", flush=True)

        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
