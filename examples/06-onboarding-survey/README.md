# 🧑‍🚀 New Customer Onboarding Survey Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa` listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html) —
pausing execution inline to wait for the user's next reply, instead of registering a separate
handler per step.

A 4-question onboarding survey (name, use case, team size, email) implemented as a single,
linear function — no state machine, no separate handlers per question.

## What it demonstrates

- `sent.wait_for_reply(...)` for free-text answers
- `sent.wait_for_click(...)` for quick-reply button answers
- `sent.wait_for_selection(...)` for a `SectionList` answer
- `cancelers=` (a "Cancel" button available at every step) and `timeout=` on every listener
- Handling `types.ListenerCanceled` / `types.ListenerTimeout` in one place for the whole flow
- A manual retry loop (email validation) without any extra handlers

## ⚠️ Before you run this in production

Listeners block the current task/thread until the user replies. Read the
[Limitations and Resource Safety Warnings](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html)
in the docs — in short: always set a `timeout` (done here), and prefer `pywa_async` (used here)
over the sync client if you expect concurrent conversations, since sync listeners each block a
worker thread.

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/06-onboarding-survey
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

Send `hi` (or `/start`) to the bot and answer each prompt: your name, your use case (buttons),
your team size (a list), and your email (free text, validated with a retry loop). Tap "Cancel" at
any point to bail out, or just don't reply for 2 minutes to see the timeout message.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 06-onboarding-survey --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
