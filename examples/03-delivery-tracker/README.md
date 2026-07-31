# 📬 Delivery Status Notifier Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa` updates](https://pywa.readthedocs.io/en/latest/content/updates/overview.html) —
specifically `MessageStatus` (sent/delivered/read/failed) paired with callback buttons, so you
know exactly what happened to an outbound notification instead of firing it and hoping for the best.

## What it demonstrates

- `@wa.on_message_status` with `filters.sent` / `filters.delivered` / `filters.read` / `filters.failed`
- `filters.failed_with(...)` to react specifically to `errors.MessageUndeliverable` /
  `errors.ReEngagementMessage` (e.g. the customer's 24h service window closed) and fall back to a
  human channel
- The `tracker` parameter on `send_message(...)` to correlate a later `MessageStatus` update back
  to the order it belongs to
- `@wa.on_callback_button` for the "Confirm receipt" / "Report an issue" buttons attached to the
  notification itself

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/03-delivery-tracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

## Run

```bash
pywa dev
```

## Try it

1. From your own WhatsApp, send `/ship A1234` to the bot's number — this simulates your backend
   notifying you that order `A1234` shipped.
2. Watch the terminal logs: `on_sent` → `on_delivered` → `on_read` fire as WhatsApp reports each
   stage back to your webhook.
3. Tap "✅ Confirm receipt" or "⚠️ Report an issue" on the notification to see the callback-button
   handlers respond (and, if `STAFF_NUMBER` is set, alert a human).
4. To see the failure path, set `STAFF_NUMBER` and send `/ship` to a number outside your allowed
   test list, or one that hasn't messaged you in the last 24h — WhatsApp will report the send as
   failed and `on_undeliverable` will alert the staff number.

## Notes

`ORDERS` is an in-memory dict for clarity — replace it with your real order-management system.
In production, `notify_shipment` would be triggered by your backend (a shipping webhook, a cron
job, etc.), not by a chat command; the `/ship` command here exists purely to make the example
self-contained and runnable without extra infrastructure.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 03-delivery-tracker --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
