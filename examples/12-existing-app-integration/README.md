# 🧩 Existing FastAPI App Integration

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** the [`WhatsApp` client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)'s
`server=` parameter — attaching pywa's webhook to an app you already own, instead of letting pywa
create and manage its own server.

Every other example in this gallery lets pywa create its own server (run via `pywa dev`/`pywa run`).
This one is the opposite: `app = FastAPI(...)` is created *first*, with its own unrelated routes
(`/`, `/health`), and pywa is handed that app via `server=app` — exactly what you'd do if your
WhatsApp bot is one feature bolted onto an existing product API.

## What it demonstrates

- `WhatsApp(server=app, ...)` — attach to an existing Flask/FastAPI app instead of a pywa-managed one
- `webhook_endpoint="/webhook/whatsapp"` — required here, since the app already uses `/` for its
  own route and pywa's default webhook path is also `/`
- Why `pywa dev`/`pywa run` refuse to run this file (see below) and what to use instead

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/12-existing-app-integration
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

## Run

```bash
fastapi dev main.py
```

**Not `pywa dev`/`pywa run`.** Those commands exist to run a server *for* you — they explicitly
refuse to start if the `WhatsApp` instance was already given a `server=`, since in that case the
app's lifecycle isn't pywa's to manage. When you own the app, you run it the same way you'd run
any other FastAPI/Flask app (`fastapi dev`/`fastapi run`, `uvicorn main:app`, `flask run`, a
production ASGI/WSGI server, etc.).

## Try it

- `curl http://localhost:8000/health` → your own route, unrelated to WhatsApp, works as normal.
- Send the bot a text message on WhatsApp → it echoes it back, handled through
  `/webhook/whatsapp` on the same app and port.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 12-existing-app-integration --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead (swap `fastapi dev` for `flask --app main run` if you also switch `server=` to a
Flask app — both are supported).
