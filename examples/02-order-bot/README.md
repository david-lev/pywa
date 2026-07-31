# 🍕 Quick-Serve Restaurant Ordering Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa.types`](https://pywa.readthedocs.io/en/latest/content/types/overview.html) —
interactive keyboards (`SectionList`, `Button`, `URLButton`) and media replies.

A restaurant ordering bot: browse a categorized menu, tap items to see details and photos, add
them to a cart, and check out — all without leaving WhatsApp.

## What it demonstrates

- `types.SectionList` / `types.Section` / `types.SectionRow` to present a categorized menu
- `types.Button` quick-reply buttons to drive a stateful cart (add / view / clear / checkout)
- `types.URLButton` on the checkout confirmation (opens an order-tracking page)
- Replying with an image (`sel.reply_image(...)`) for menu items that have a photo
- `on_callback_selection` (list row tapped) vs `on_callback_button` (quick-reply button tapped)

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/02-order-bot
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

1. Send `menu` (or `hi`) → a section list of categories/items appears.
2. Tap an item → its details (and photo, for mains) are shown with "Add to cart" / "View cart".
3. Tap "Add to cart" a few times, then "View cart" to see the running total.
4. Tap "Checkout" → order confirmation with a "Track your order" link button.

## Notes

The menu and cart are kept in memory (`MENU`, `CARTS` dicts) for clarity — swap them for a real
catalog/database and persistent storage in production. For a larger catalog you may prefer pywa's
native WhatsApp Catalog support (`wa.send_catalog` / `wa.send_product`) instead of a hand-rolled menu.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 02-order-bot --async` to fetch
it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`) version instead.
