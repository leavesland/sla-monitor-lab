# SLA Monitor (demo)

The smallest uptime monitor that actually works. Pings a list of URLs every
10 seconds, keeps the last 60 results per URL in memory, and shows a live page.

```
Monitor/
├── main.py           # the server: background checker + two endpoints
├── index.html        # the dashboard page
├── requirements.txt
└── README.md
```

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000

## How it fits together

```
uvicorn starts
   └─ lifespan() starts checker_loop() in the background
        └─ every 10 s: check_one() for every TARGET, all at once
             └─ appends {ok, status, latency_ms} to history[name]

browser opens /            → gets index.html
index.html every 5 s       → fetch /api/status → redraw cards
/api/status                → reads history, computes uptime %, returns JSON
```

Two endpoints, one background loop, one dictionary of deques. That is the
whole thing.

## What is missing on purpose

- **No database.** Restart the server and history is gone.
- **No alerts.** Nothing emails you when a target goes down.
- **No auth.** Anyone who can reach the port can see the page.
- **One process.** The checker runs inside the web server. If the checker
  hangs, the page hangs. A real monitor puts the checker in its own worker.
