"""
Existing FastAPI App Integration
===================================
Feature focus: mounting pywa onto an app you already own (`server=...`), instead of letting pywa
create and manage its own server. Useful when your WhatsApp bot is one feature of a larger API
that already has its own routes, middleware, auth, etc.
"""

import os

import dotenv
from fastapi import FastAPI

from pywa_async import WhatsApp, filters, types
from pywa_async.utils import start_ngrok_tunnel

dotenv.load_dotenv()

# This is *your* app — imagine it already has dozens of routes, middleware, a database
# connection pool, etc. pywa just attaches a webhook route to it; it doesn't own or replace it.
app = FastAPI(title="My Product API")


@app.get("/")
async def root():
    return {"service": "my-product-api", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


callback_url = os.getenv("CALLBACK_URL")
if not callback_url:
    callback_url = start_ngrok_tunnel(auth_token=os.environ["NGROK_AUTH_TOKEN"])

wa = WhatsApp(
    phone_id=os.environ["WHATSAPP_PHONE_ID"],
    token=os.environ["WHATSAPP_TOKEN"],
    app_id=os.environ["WHATSAPP_APP_ID"],
    app_secret=os.environ["WHATSAPP_APP_SECRET"],
    server=app,  # attach to the app above instead of letting pywa create its own
    webhook_endpoint="/webhook/whatsapp",  # avoid clashing with the app's own "/" route
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
)


@wa.on_message(filters.text)
async def echo(_: WhatsApp, msg: types.Message):
    await msg.reply(f"You said: {msg.text}")


# Run with: fastapi dev main.py  (NOT `pywa dev` — see README.md for why)
