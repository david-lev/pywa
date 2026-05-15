# 07 — Full async bot

Identical surface to the sync examples, but built on `pywa_async`. Every method that does I/O (`send_*`, `reply_*`, `react`, `download`, `wait_for_*`) becomes a coroutine.

## What changes vs sync

| Sync (`pywa`) | Async (`pywa_async`) |
|---|---|
| `from pywa import WhatsApp` | `from pywa_async import WhatsApp` |
| `def handler(...)` | `async def handler(...)` |
| `msg.reply_text(...)` | `await msg.reply_text(...)` |
| `wa.send_image(...)` | `await wa.send_image(...)` |

Nothing else — types, filters, listeners, flows, templates: all identical.

## Run

```bash
cp ../.env.example .env
fastapi dev main.py
```

Try:
- `ping` → `pong`
- `joke` → fetches a random joke from a public API (concurrent with reacting)
- anything else → echo

## When to choose async

- You call other async APIs (`httpx.AsyncClient`, `asyncpg`, `aioredis`, OpenAI/Anthropic SDKs in async mode).
- You handle high concurrency and a sync handler would block FastAPI's event loop.
- You want streaming responses (e.g. token-by-token replies from an LLM).

For simple bots, the sync API is just as fast and easier to debug.
