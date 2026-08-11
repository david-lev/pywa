# 🏦 Loan Application Flow Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [WhatsApp Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html) —
rich, multi-screen forms rendered natively inside WhatsApp, with your server validating each step.

Instead of a clunky back-and-forth chat, the applicant fills out a real form: personal details →
loan amount & purpose → a server-computed review screen → submit. This is the pattern you'd use
for loan applications, job applications, sign-ups, or any structured-data collection flow.

## What it demonstrates

- Defining a `FlowJSON` with multiple screens (`flow_json.py`): `TextInput`, `RadioButtonsGroup`,
  `Dropdown`, `Footer`
- A dynamic flow: each screen's `Footer` uses `DataExchangeAction` to hand control back to your
  server via `@wa.on_flow_request(...).on_data_exchange(screen=...)`
- Server-side validation with `error_message=` (e.g. rejecting an invalid email or out-of-range
  loan amount without leaving the screen)
- Computing a result server-side (estimated monthly payment) and injecting it into the next
  screen with `ScreenData`
- Sending the flow with `types.FlowButton` and receiving the result with `@wa.on_flow_completion`
- End-to-end encryption setup (`business_private_key` + `set_business_public_key`), required for
  all dynamic flows

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added, and a WhatsApp Business Account (WABA) ID
- `pip install "pywa[cryptography]"` (bundled in `requirements.txt`) for flow encryption/decryption
- A **stable** public HTTPS URL — a static ngrok domain or a real deployment. Flows are registered
  against a fixed endpoint URL, so a URL that changes on every restart will break them.

## Setup

```bash
cd examples/05-loan-application-flow
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Generate an encryption key pair** (required for dynamic flows):

```bash
openssl genrsa -des3 -out private.pem 2048
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
```

Fill in `.env` with your credentials, plus a stable `CALLBACK_URL` (e.g. `pywa dev` will print
one if you set `NGROK_AUTH_TOKEN` and a static `domain=` — see
[`start_ngrok_tunnel`](https://pywa.readthedocs.io/en/latest/content/client/overview.html) — or
use your real domain).

**One-time step — create the flow:**

```bash
python3 setup_flow.py
```

Copy the printed flow ID into `LOAN_FLOW_ID` in `.env`.

## Run

```bash
pywa dev
```

## Try it

1. Send `/apply` to the bot.
2. Tap "Start Application" → fill in your name, email and employment status.
3. Enter a loan amount and purpose — try an invalid amount (e.g. `0` or `999999`) to see the
   inline validation error.
4. Review the computed estimated monthly payment, then tap "Submit Application".
5. The bot replies once it receives the flow completion.

## Notes

`APPLICATIONS` is an in-memory dict keyed by `flow_token` (the customer's WhatsApp ID here) — swap
it for a real database in production. The flow is sent with `mode=FlowStatus.DRAFT` so you can
test it right away; switch to `FlowStatus.PUBLISHED` (and publish the flow in WhatsApp Manager)
before going live.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 05-loan-application-flow --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
