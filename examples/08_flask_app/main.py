"""
08 — Flask alternative

Identical bot to 01_echo_bot, but running on Flask instead of FastAPI.
Shows that `server=` accepts either.

Run:
    cp ../.env.example .env
    pip install "pywa[flask,cryptography]" python-dotenv
    flask --app main run --port 8000 --debug
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask

from pywa import WhatsApp, filters, types

load_dotenv()
logging.basicConfig(level=logging.INFO)

flask_app = Flask(__name__)

wa = WhatsApp(
    phone_id=os.environ["WA_PHONE_ID"],
    token=os.environ["WA_TOKEN"],
    server=flask_app,
    callback_url=os.environ["WA_CALLBACK_URL"],
    verify_token=os.environ["WA_VERIFY_TOKEN"],
    app_id=int(os.environ["WA_APP_ID"]),
    app_secret=os.environ["WA_APP_SECRET"],
)


@wa.on_message(filters.text)
def echo(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text(msg.text)


@wa.on_message
def wave(_: WhatsApp, msg: types.Message) -> None:
    msg.react("👋")


# A normal Flask route alongside the WhatsApp webhook — they coexist on the same app.
@flask_app.route("/health")
def health() -> dict:
    return {"status": "ok"}
