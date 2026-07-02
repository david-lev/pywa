# 01 — Echo bot

Minimal PyWa bot. Replies with the same text it received; reacts 👋 to anything else.

## Run

```bash
cp ../.env.example .env       # fill in WA_PHONE_ID, WA_TOKEN, WA_VERIFY_TOKEN, WA_APP_ID, WA_APP_SECRET, WA_CALLBACK_URL
pip install -r ../requirements.txt
fastapi dev main.py
```

In another terminal:

```bash
ngrok http 8000
```

Copy the `https://…ngrok.io` URL into `WA_CALLBACK_URL` and restart `fastapi dev`. Send a WhatsApp message to your test number — you'll get the same text back.

## What to look at

- [`main.py:39`](main.py#L39) — `@wa.on_message(filters.text)` registers a handler that only fires for text messages.
- [`main.py:45`](main.py#L45) — the unfiltered `@wa.on_message` decorator catches everything else.
- `wa.send_message(...)` is replaced by `msg.reply_text(...)` — the same call, but PyWa fills in the `to` and `reply_to_message_id` for you.
