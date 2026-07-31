# 🛠️ WhatsApp-Native Admin Console Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** the [`WhatsApp` client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)'s
business-management API — reading/updating your business profile and commerce settings, and
checking phone number health, all from chat commands. No separate admin dashboard required.

## What it demonstrates

- `wa.get_business_profile()` / `wa.update_business_profile(about=..., description=...)`
- `wa.get_commerce_settings()` / `wa.update_commerce_settings(is_cart_enabled=..., is_catalog_visible=...)`
- `wa.get_business_phone_number()` for quality rating / messaging limit tier / status
- Gating access with a custom `is_admin` filter built from `filters.from_users(...)`

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/08-business-profile-manager
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — set ADMIN_NUMBERS to your own WhatsApp ID!
```

## Run

```bash
pywa dev
```

## Try it

From an `ADMIN_NUMBERS` number, send `/help` to see the command list, then try:

- `/profile` — view the current business profile
- `/set_about We build great coffee ☕` — update the "about" text
- `/commerce` — view catalog/cart settings
- `/cart on` / `/catalog off` — toggle commerce settings
- `/number_info` — check your phone number's quality rating and messaging limit tier

From any other number, every command is met with "not authorized".

## Notes

This bot doesn't persist any state of its own — every command reads/writes directly against the
Graph API, so `/profile` and `/commerce` always reflect what's live on your account.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 08-business-profile-manager --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
