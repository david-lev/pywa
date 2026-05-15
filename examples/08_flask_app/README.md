# 08 — Flask alternative

Same echo bot as example 01, on Flask. The only differences vs FastAPI:

- `from flask import Flask` instead of `from fastapi import FastAPI`.
- Launched with `flask --app main run`.
- You can mount normal Flask routes (`/health` here) alongside the WhatsApp webhook.

## Run

```bash
cp ../.env.example .env
pip install "pywa[flask,cryptography]" python-dotenv
flask --app main run --port 8000 --debug
```

Then expose it with `ngrok http 8000` and put that URL in `WA_CALLBACK_URL`.

## Notes

- For production, run Flask behind a real WSGI server (`gunicorn`, `uwsgi`). The dev server is single-threaded and not suitable for webhooks at scale.
- Async handlers are still possible on Flask if you install `flask[async]` — but for fully-async stacks, prefer FastAPI / Starlette and the `pywa_async` package (see example 07).
