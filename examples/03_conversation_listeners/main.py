"""
03 — Conversation with listeners

A multi-turn sign-up flow built without state machines or external storage —
just `wait_for_reply` and `wait_for_click`. Each step blocks the handler
until the user responds (with timeout + cancel buttons).

Try it: send "/signup" to the bot.

Run:
    cp ../.env.example .env
    fastapi dev main.py
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from pywa import WhatsApp, filters, types
from pywa.listeners import ListenerCanceled, ListenerTimeout

load_dotenv()
logging.basicConfig(level=logging.INFO)

fastapi_app = FastAPI()

wa = WhatsApp(
    phone_id=os.environ["WA_PHONE_ID"],
    token=os.environ["WA_TOKEN"],
    server=fastapi_app,
    callback_url=os.environ["WA_CALLBACK_URL"],
    verify_token=os.environ["WA_VERIFY_TOKEN"],
    app_id=int(os.environ["WA_APP_ID"]),
    app_secret=os.environ["WA_APP_SECRET"],
)

CANCEL = filters.callback_button & filters.matches("cancel")
TIMEOUT_SECS = 120.0


@wa.on_message(filters.command("signup"))
def signup(_: WhatsApp, msg: types.Message) -> None:
    try:
        # Step 1: name (any text)
        name = msg.reply(
            text="Welcome! What's your name?",
            buttons=[types.Button(title="Cancel", callback_data="cancel")],
        ).wait_for_reply(
            filters=filters.text,
            cancelers=CANCEL,
            timeout=TIMEOUT_SECS,
        ).text

        # Step 2: age (text that's a positive integer)
        age_msg = msg.reply(
            text=f"Nice to meet you, {name}! How old are you?",
            buttons=[types.Button(title="Cancel", callback_data="cancel")],
        ).wait_for_reply(
            filters=filters.text
            & filters.new(lambda _, m: m.text.isdigit() and 1 <= int(m.text) <= 120),
            cancelers=CANCEL,
            timeout=TIMEOUT_SECS,
        )
        age = int(age_msg.text)

        # Step 3: confirmation (button click)
        confirm = msg.reply(
            text=f"You are *{name}*, age *{age}*. Is that correct?",
            buttons=[
                types.Button(title="✅ Yes", callback_data="confirm"),
                types.Button(title="🔁 Restart", callback_data="restart"),
                types.Button(title="Cancel", callback_data="cancel"),
            ],
        ).wait_for_click(
            cancelers=CANCEL,
            timeout=TIMEOUT_SECS,
        )

        if confirm.data == "confirm":
            confirm.reply_text(f"All set, {name}! 🎉")
        elif confirm.data == "restart":
            confirm.reply_text("No worries — send /signup to start over.")

    except ListenerTimeout:
        msg.reply_text("⌛ Timed out. Send /signup to try again.")
    except ListenerCanceled:
        msg.reply_text("Cancelled. Send /signup whenever you're ready.")


@wa.on_message
def hint(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text("Send /signup to start.")
