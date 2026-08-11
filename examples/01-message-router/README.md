# 🧭 Smart Support Router Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa.filters`](https://pywa.readthedocs.io/en/latest/content/filters/overview.html) —
composable conditions that decide which updates a handler receives.

A small business support bot that routes incoming messages using nothing but filters: a
keyword-based FAQ, a `/human` escalation command, an attachment acknowledgement, a denylist for
abusive numbers, and a catch-all fallback — all without a single `if`/`else` chain.

## What it demonstrates

- Combining filters with `&`, `|`, and `~` (`filters.command(...) & ~is_blocked`)
- Built-in filters: `filters.command`, `filters.contains`, `filters.media`, `filters.text`
- Writing a custom filter with `@filters.new`
- Relying on handler registration order + the default "first match wins" dispatch to build a
  routing table (specific routes first, generic fallback last)

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added ([Get Started guide](https://pywa.readthedocs.io/en/latest/content/getting-started.html))
- Your Phone Number ID, temporary/permanent token, App ID and App secret

## Setup

```bash
cd examples/01-message-router
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

## Run

```bash
pywa dev
```

`pywa dev` starts a local server with hot-reload and (if `CALLBACK_URL` is empty) opens a
temporary ngrok tunnel so Meta can reach your webhook. Point your Meta App's webhook to the
printed URL and subscribe to the `messages` field.

## Try it

Send the bot a message on WhatsApp:

- `hi` → greeting
- `what's your shipping policy?` → FAQ match on "shipping"
- `I want a refund` → FAQ match on "return"
- `/human` → forwarded to `SUPPORT_AGENT_NUMBER`
- send a photo/document → attachment acknowledgement
- anything else → fallback message

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 01-message-router --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
