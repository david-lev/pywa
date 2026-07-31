# 🎫 Multi-Channel Helpdesk Ticket Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa` handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html) —
registering several handlers for the same update type and controlling how they interact.

Customers open tickets with `/ticket <description>`; staff numbers close them with
`/close <ticket_id>`. The interesting part isn't the ticketing logic — it's how the handlers are
wired together.

## What it demonstrates

- `priority=` — `audit_log` runs before anything else on every message
- `continue_handling=True` (client-wide) — lets multiple matching handlers run per update instead
  of only the first match, so the audit log always runs alongside the "real" handler
- `msg.stop_handling()` — used inside `open_ticket`/`close_ticket` to opt back out of that fan-out
  once they've fully handled the update, so the generic `fallback` handler doesn't also fire
- `@wa.on_edited_message` / `@wa.on_deleted_message` alongside `@wa.on_message`

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/07-helpdesk-ticket-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials (STAFF_NUMBERS is your own WhatsApp ID, for testing /close)
```

## Run

```bash
pywa dev
```

## Try it

1. Send `/ticket My printer isn't working` → a ticket ID is created (watch the terminal: the
   audit log line prints *and* the ticket confirmation is sent — both handlers ran).
2. From a number listed in `STAFF_NUMBERS`, send `/close T0001` (using the ticket ID from step 1)
   → the ticket closes and the original customer is notified.
3. Send any other text → the generic fallback responds (only when nothing more specific matched
   and stopped propagation first).
4. Edit or delete a message you sent to the bot → watch the terminal for the edit/delete audit
   lines.

## Notes

`TICKETS` is an in-memory dict for clarity — replace it with a real ticketing system/database in
production. `continue_handling=True` is a deliberate, non-default choice made here purely to
demonstrate the interaction between it and `stop_handling()`; most bots are fine with the default
(`False`, only the first matching handler runs).

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 07-helpdesk-ticket-bot --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
