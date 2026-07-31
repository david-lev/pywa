# ruff: noqa: T201
"""
Multi-Channel Helpdesk Ticket Bot
===================================
Feature focus: `pywa` handlers — registering multiple handlers for the same update type and
controlling how they interact via `priority`, `continue_handling`, and `stop_handling()`.
"""

import itertools
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
    # By default only the *first* matching handler for an update runs. Setting this to True lets
    # every matching handler run (e.g. our always-on audit_log below), and individual handlers can
    # still opt out early with `.stop_handling()`.
    continue_handling=True,
)

STAFF_NUMBERS = {
    n.strip() for n in os.getenv("STAFF_NUMBERS", "").split(",") if n.strip()
}

_next_ticket_id = itertools.count(1)
TICKETS: dict[str, dict] = {}  # ticket_id -> {customer, description, status}


@wa.on_message(priority=10)
async def audit_log(_: WhatsApp, msg: types.Message):
    """
    Registered with the highest priority so it always runs first — and thanks to
    `continue_handling=True`, it runs *alongside* whichever handler below also matches, instead of
    replacing it. Useful for logging/metrics that shouldn't interfere with business logic.
    """
    print(f"[audit] {msg.from_user.bsuid}: {msg.text!r}")


@wa.on_message(filters.command("ticket", ignore_case=True), priority=5)
async def open_ticket(_: WhatsApp, msg: types.Message):
    ticket_id = f"T{next(_next_ticket_id):04d}"
    description = msg.text.partition(" ")[2] or "(no description provided)"
    TICKETS[ticket_id] = {
        "customer": msg.from_user.bsuid,
        "description": description,
        "status": "open",
    }
    await msg.reply(
        f"🎫 Ticket {ticket_id} opened. Our team will get back to you soon."
    )
    # Without continue_handling=True this would be unnecessary (only one handler ever runs), but
    # since we opted into fan-out above, we explicitly stop here so the generic fallback handler
    # further down doesn't *also* reply to this same message.
    msg.stop_handling()


@wa.on_message(
    filters.from_users(*STAFF_NUMBERS) & filters.command("close", ignore_case=True),
    priority=5,
)
async def close_ticket(_: WhatsApp, msg: types.Message):
    ticket_id = msg.text.split(maxsplit=1)[1].upper() if " " in msg.text else None
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        await msg.reply(f"No such ticket: {ticket_id}")
    else:
        ticket["status"] = "closed"
        await msg.reply(f"✅ Ticket {ticket_id} closed.")
        await wa.send_message(
            to=ticket["customer"],
            text=f"Your ticket {ticket_id} has been resolved and closed. Thanks for your patience!",
        )
    msg.stop_handling()


@wa.on_message(filters.text)
async def fallback(_: WhatsApp, msg: types.Message):
    await msg.reply("Send /ticket <description> to open a support ticket.")


@wa.on_edited_message
async def on_edit(_: WhatsApp, edited: types.EditedMessage):
    print(f"[audit] {edited.from_user.bsuid} edited their message to: {edited.text!r}")


@wa.on_deleted_message
async def on_delete(_: WhatsApp, deleted: types.DeletedMessage):
    print(f"[audit] a message from {deleted.from_user.bsuid} was deleted")


# Run with: pywa dev
