"""
Smart Support Router Bot
=========================
Feature focus: `pywa.filters` — composable conditions that decide which updates a handler receives.

A small business support bot that routes incoming messages to the right reply using nothing but
filters: a keyword-based FAQ, a "/human" escalation command, an attachment acknowledgement, a
denylist for abusive numbers, and a catch-all fallback. No if/else chains — the routing logic lives
entirely in the filters attached to each handler.
"""

import os

import dotenv

from pywa_async import WhatsApp, filters, types
from pywa_async.utils import start_ngrok_tunnel

dotenv.load_dotenv()

callback_url = os.getenv("CALLBACK_URL")
if not callback_url:
    callback_url = start_ngrok_tunnel(auth_token=os.environ["NGROK_AUTH_TOKEN"])

wa = WhatsApp(
    phone_id=os.environ["WHATSAPP_PHONE_ID"],
    token=os.environ["WHATSAPP_TOKEN"],
    app_id=os.environ["WHATSAPP_APP_ID"],
    app_secret=os.environ["WHATSAPP_APP_SECRET"],
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
)

# Users that are not allowed to interact with the bot (comma separated BSUIDs).
# `from_user.wa_id` is the phone number, but it's optional now — it's unavailable for users who've
# enabled WhatsApp usernames — so `bsuid` (always present) is the identifier to key a denylist on.
BLOCKED_BSUIDS = {
    n.strip() for n in os.getenv("BLOCKED_BSUIDS", "").split(",") if n.strip()
}

# Where escalated conversations get forwarded to (a real support agent's WhatsApp number)
SUPPORT_AGENT_NUMBER = os.getenv("SUPPORT_AGENT_NUMBER")


@filters.new
def is_blocked(_: WhatsApp, msg: types.Message) -> bool:
    """A custom filter — any callable that takes (client, update) and returns a bool."""
    return msg.from_user.bsuid in BLOCKED_BSUIDS


# Handlers are tried in registration order; the first one whose filter matches wins.
# So we register the most specific routes first and a generic fallback last.


@wa.on_message(filters.command("start", "hi", "hello", ignore_case=True) & ~is_blocked)
async def greet(_: WhatsApp, msg: types.Message):
    await msg.react("👋")
    await msg.reply(
        f"Hi {msg.from_user.name}! I'm the support bot. Ask me about *shipping*, "
        "*returns* or *pricing* — or send /human to talk to a real person."
    )


@wa.on_message(filters.command("human", "agent", ignore_case=True) & ~is_blocked)
async def escalate(_: WhatsApp, msg: types.Message):
    await msg.reply("🙋 Connecting you with a human agent — hang tight!")
    if SUPPORT_AGENT_NUMBER:
        await wa.send_message(
            to=SUPPORT_AGENT_NUMBER,
            text=f"📨 {msg.from_user.name} ({msg.from_user.wa_id or msg.from_user.bsuid}) asked for a human:\n\n{msg.text}",
        )


@wa.on_message(
    filters.contains("shipping", "delivery", "ship", ignore_case=True) & ~is_blocked
)
async def faq_shipping(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "📦 Orders ship within 1-2 business days and arrive in 3-5 days domestically."
    )


@wa.on_message(
    filters.contains("return", "refund", "exchange", ignore_case=True) & ~is_blocked
)
async def faq_returns(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "↩️ You can return any item within 30 days for a full refund — "
        "just reply with your order number."
    )


@wa.on_message(
    filters.contains("price", "pricing", "cost", "how much", ignore_case=True)
    & ~is_blocked
)
async def faq_pricing(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "💰 Pricing depends on the plan. Send /human if you'd like a custom quote."
    )


@wa.on_message(filters.media & ~is_blocked)
async def handle_attachment(_: WhatsApp, msg: types.Message):
    await msg.react("📥")
    await msg.reply("Thanks, we received your file — an agent will review it shortly.")


@wa.on_message(filters.text & ~is_blocked)
async def fallback(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "🤔 I didn't catch that. Try *shipping*, *returns*, *pricing*, or /human."
    )


# Run with: pywa dev
