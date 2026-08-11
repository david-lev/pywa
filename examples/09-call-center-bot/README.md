# 📞 Voice Call-Back Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** the [WhatsApp Calling API](https://pywa.readthedocs.io/en/latest/content/calls/overview.html)
(`pywa.types.calls`) — requesting call permission, initiating/accepting calls, and reacting to the
full call lifecycle.

A customer texts `/call_me`; the bot checks whether it already has permission to call them, asks
for it if not, and calls back once granted. It also answers inbound calls placed directly to the
business number.

## ⚠️ Important: this covers call *signaling*, not audio

pywa transports call signaling — permissions, SDP offers/answers, and lifecycle events (ringing,
answered, rejected, terminated). It does **not** negotiate or carry audio. A production
integration needs a real WebRTC/VoIP media stack (e.g. a browser/mobile `RTCPeerConnection`, or a
server-side SFU) to generate genuine SDP answers and handle the actual RTP audio stream. This
example sends a static placeholder SDP (`answer.sdp`) so you can exercise the full call-handling
flow end-to-end without that extra infrastructure — real calls made this way will connect
signaling-wise but won't carry usable audio.

## What it demonstrates

- `wa.get_call_permissions(from_user=...)` and `types.CallPermissionRequestButton`
- `@wa.on_call_permission_update` with `filters.call_permission_accepted` / `_rejected`
- `wa.initiate_call(...)` to call a user back
- `@wa.on_call_connect` with `filters.incoming_call`, and the `call.pre_accept()` / `call.accept()`
  shortcuts
- `@wa.on_call_status` with `filters.call_ringing` / `call_answered` / `call_rejected`
- `@wa.on_call_terminate` for logging call outcome/duration

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added, with **Calling** enabled for your phone number

## Setup

```bash
cd examples/09-call-center-bot
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

1. Send `/call_me` to the bot.
2. If you haven't granted call permission before, you'll be asked to allow calls — accept or
   reject it and watch the corresponding handler fire.
3. Once permission is granted, the bot calls you back (signaling-wise — see the caveat above).
4. Watch the terminal for `on_ringing` → `on_answered`/`on_call_status_rejected` →
   `on_call_terminate` as the call progresses.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 09-call-center-bot --async` to
fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`) version
instead.
