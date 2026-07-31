# ruff: noqa: T201
"""
Delivery Status Notifier Bot
=============================
Feature focus: `pywa` updates — specifically `MessageStatus` (sent/delivered/read/failed) combined
with callback buttons, so you can know exactly what happened to an outbound notification and react
to it, instead of firing a message and hoping for the best.
"""

import os

import dotenv

from pywa_async import WhatsApp, errors, filters, types
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

# WhatsApp number of a staff member to alert when a notification can't be delivered
STAFF_NUMBER = os.getenv("STAFF_NUMBER")

# order_id -> {"customer": bsuid, "status": str}. Swap for a real database in production.
ORDERS: dict[str, dict] = {}


@wa.on_message(filters.command("ship", ignore_case=True))
async def notify_shipment(_: WhatsApp, msg: types.Message):
    """
    Demo trigger: `/ship <order_id>` simulates your order-management system notifying a
    customer that their order shipped. In production this would be called from your own
    backend (e.g. a webhook from your shipping provider), not from a chat command.
    """
    order_id = msg.text.split(maxsplit=1)[1] if " " in msg.text else "A1001"
    ORDERS[order_id] = {"customer": msg.from_user.bsuid, "status": "pending"}
    try:
        await wa.send_message(
            to=msg.from_user.bsuid,
            text=f"📦 Order *{order_id}* has shipped! Estimated arrival: 2 days.",
            buttons=[
                types.Button(
                    title="✅ Confirm receipt",
                    callback_data=f"order:confirm:{order_id}",
                ),
                types.Button(
                    title="⚠️ Report an issue", callback_data=f"order:issue:{order_id}"
                ),
            ],
            tracker=order_id,  # lets us match the later MessageStatus update back to this order
        )
    except errors.WhatsAppError as e:
        await msg.reply(f"❌ Couldn't send the notification: {e}")
        return
    await msg.reply(
        f"Notification sent for order {order_id}, tracking its delivery status…"
    )


@wa.on_message_status(filters.sent)
async def on_sent(_: WhatsApp, status: types.MessageStatus):
    order_id = status.tracker
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "sent"
        print(f"[{order_id}] left our servers")


@wa.on_message_status(filters.delivered)
async def on_delivered(_: WhatsApp, status: types.MessageStatus):
    order_id = status.tracker
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "delivered"
        print(f"[{order_id}] delivered to the customer's device")


@wa.on_message_status(filters.read)
async def on_read(_: WhatsApp, status: types.MessageStatus):
    order_id = status.tracker
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "read"
        print(f"[{order_id}] read by the customer")


@wa.on_message_status(
    filters.failed_with(errors.MessageUndeliverable, errors.ReEngagementMessage)
)
async def on_undeliverable(_: WhatsApp, status: types.MessageStatus):
    """
    These specific failures usually mean the customer's 24h service window is closed or their
    number can't receive the message — a good moment to fall back to a human-initiated channel.
    """
    order_id = status.tracker
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "failed"
    if STAFF_NUMBER:
        await wa.send_message(
            to=STAFF_NUMBER,
            text=f"⚠️ Delivery notification for order {order_id} failed ({status.error.code}: "
            f"{status.error.message}). Please call the customer directly.",
        )


@wa.on_message_status(filters.failed)
async def on_other_failure(_: WhatsApp, status: types.MessageStatus):
    order_id = status.tracker
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "failed"
    print(f"[{order_id}] failed to send: {status.error}")


@wa.on_callback_button(filters.startswith("order:confirm:"))
async def confirm_receipt(_: WhatsApp, clb: types.CallbackButton):
    order_id = clb.data.split(":")[2]
    await clb.react("📬")
    await clb.reply(f"Great, thanks for confirming order {order_id}! Enjoy 🎉")


@wa.on_callback_button(filters.startswith("order:issue:"))
async def report_issue(_: WhatsApp, clb: types.CallbackButton):
    order_id = clb.data.split(":")[2]
    await clb.reply("Sorry to hear that! A support agent will reach out shortly.")
    if STAFF_NUMBER:
        await wa.send_message(
            to=STAFF_NUMBER,
            text=f"🚨 {clb.from_user.name} reported an issue with order {order_id}.",
        )


# Run with: pywa dev
