# 🔐 Account Verification (OTP) Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa` message templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html) —
sending a pre-approved *authentication* template to deliver a one-time code, then verifying it.

Templates are the only way to message a user outside a 24-hour customer service window, and
authentication templates are WhatsApp's purpose-built format for OTP delivery (fixed, compliant
copy + a "Copy Code" button) — this is exactly how apps send WhatsApp-based login codes.

## What it demonstrates

- Defining an authentication `Template` (`AuthenticationBody`, `AuthenticationFooter`,
  `CopyCodeOTPButton`) and creating it with `wa.create_template(...)`
- Tracking approval with `@wa.on_template_status_update`
- Sending it with `wa.send_template(...)` and per-component `.params(otp=...)`
- Verifying the reply with a listener (`sent.wait_for_reply(...)`)

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added, and a WhatsApp Business Account (WABA) ID

## Setup

```bash
cd examples/04-otp-verification
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

**One-time step — create the template:**

```bash
python3 setup_template.py
```

Then wait for Meta to approve it (usually minutes to a few hours) before continuing — check the
WhatsApp Manager dashboard or watch for the `on_template_status_update` log line once `main.py`
is running.

## Run

```bash
pywa dev
```

## Try it

1. Send `/verify` to the bot.
2. It sends you an authentication-template message with a 6-digit code and a "Copy Code" button.
3. Tap the button (it copies the code to your clipboard) and paste/send it back as a plain
   message.
4. The bot confirms if it matches, or lets you retry with `/verify` again. `/cancel` aborts, and
   the listener times out automatically after 5 minutes.

## Notes

`VERIFIED_USERS` is an in-memory set for clarity — persist verification state in a real database
in production. Authentication templates have fixed, non-editable body/footer text (only the
button label can be customized) since WhatsApp reviews them for compliance — see the
[Authentication Templates guide](https://pywa.readthedocs.io/en/latest/content/templates/overview.html#authentication-templates)
for the other OTP button types (`OneTapOTPButton`, `ZeroTapOTPButton`).

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 04-otp-verification --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
