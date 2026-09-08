# SLA Monitor

Two versions of the same idea, side by side.

```
Monitor/
├── simple/                 one Python file, one HTML file, everything in memory
│   ├── main.py
│   └── index.html
│
├── backend/                FastAPI + a scheduler + workers, all sharing Redis
│   ├── app/
│   │   ├── main.py         the API: reads/writes Redis, does no checking itself
│   │   ├── scheduler.py    every 10 s, puts every target name on the queue
│   │   ├── worker.py       pulls a name off the queue, checks it, records the result
│   │   ├── store.py        every Redis read and write, in one place
│   │   └── config.py       settings, overridable by environment variables
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               Next.js + TypeScript
│   ├── app/page.tsx        the dashboard page
│   ├── components/         TargetCard, Sparkline, AddTargetForm, IncidentList
│   ├── lib/api.ts          the four API calls and the two types that describe the data
│   ├── next.config.ts      forwards /api/* to the backend
│   └── Dockerfile
│
└── docker-compose.yml      redis + api + scheduler + worker + frontend
```

## Run it

Docker Desktop has to be running (whale icon in the tray, "Engine running").

```powershell
docker compose up --build
```

First run downloads images and builds two of your own; give it a few minutes.
Then:

- http://localhost:3000 — the dashboard
- http://localhost:8000/docs — the API, same auto-generated page as Project 1

Stop with Ctrl+C. Start again with `docker compose up` (no `--build` unless
you changed code). Redis keeps its data between runs because of the volume.

## The four things the simple version was missing

| Simple version | This version | Where to look |
|---|---|---|
| Checks run *inside* the web server | Checks run in **separate worker processes** | `worker.py` vs `simple/main.py` |
| Results in a Python dict, one process can see it | Results in **Redis**, every process can see it | `store.py` |
| Checks run one round at a time in one loop | A **queue**: scheduler enqueues, N workers drain it | `scheduler.py` + `store.enqueue/dequeue` |
| Vanilla HTML + JS, no types | **Next.js + TypeScript**, the API's shape is a type | `lib/api.ts` |

Plus: retries, incident open/close tracking, add and remove targets from the
page, and Docker so all five pieces start with one command.

## Things to try

**Scale the workers.** Stop it, then:

```powershell
docker compose up --scale worker=3
```

Watch the logs. Three workers with different ids take turns pulling jobs off
the same queue. That is the whole point of the queue.

**Kill the workers and watch the scheduler notice.**

```powershell
docker compose stop worker
```

After a minute the scheduler logs "backlog is N, skipping this round". The
queue is filling and nothing is draining it. Start them again with
`docker compose start worker` and the backlog drains.

**Break a target and watch an incident open.** Add a target from the page
pointing at a URL that doesn't exist. Within ten seconds it goes DOWN and an
incident appears in the sidebar. Remove the target and the incident clears.

**Look inside Redis.**

```powershell
docker compose exec redis redis-cli
> HGETALL targets
> LRANGE history:GitHub 0 4
> LLEN jobs
> KEYS *
```

That's every piece of state the system has.

## Local development without Docker for the app code

Redis still needs a container; nothing else does.

```powershell
docker run -d --name sla-redis -p 6379:6379 redis:7-alpine
```

Backend, three terminals, each with the venv active:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app.main:app --reload        # terminal 1
python -m app.scheduler              # terminal 2
python -m app.worker                 # terminal 3
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## What is still missing

- **No auth.** Anyone who reaches :3000 can add or remove targets.
- **No alerts.** Nothing emails or pings you when an incident opens.
- **No tests.** The right first test: `store.record_result` opens an
  incident on the first DOWN and closes it on the next UP.
- **No CI.** A GitHub Actions workflow that runs those tests on every push.
