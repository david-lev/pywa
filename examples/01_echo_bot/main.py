"""
01 — Echo bot

The smallest useful PyWa bot:
- Verifies its webhook on startup.
- Replies to every text message with the same text.
- Reacts with 👋 to any other message type.

Run:
    cp ../.env.example .env  # then edit the values
    fastapi dev main.py      # exposes http://localhost:8000

Expose with `ngrok http 8000` (or any tunnel) and put that URL in WA_CALLBACK_URL.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from pywa import WhatsApp, filters, types

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


@wa.on_message(filters.text)
def echo_text(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text(msg.text)


# Catch-all for anything that's not text (images, audio, contacts, ...).
@wa.on_message
def wave_back(_: WhatsApp, msg: types.Message) -> None:
    msg.react("👋")
