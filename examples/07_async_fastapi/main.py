"""
07 — Full async bot

Same API as the sync version — but every handler is `async def` and uses
`pywa_async` instead of `pywa`. Useful when you want to call async APIs
(databases, OpenAI, HTTP) from inside a handler without blocking.

Run:
    cp ../.env.example .env
    fastapi dev main.py
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

from pywa_async import WhatsApp, filters, types

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


@wa.on_message(filters.matches("ping", ignore_case=True))
async def ping(_: WhatsApp, msg: types.Message) -> None:
    await msg.reply_text("pong")


@wa.on_message(filters.matches("joke", ignore_case=True))
async def joke(_: WhatsApp, msg: types.Message) -> None:
    """Calls a public API concurrently with reacting — both happen without blocking."""
    react_task = asyncio.create_task(msg.react("🤔"))
    async with httpx.AsyncClient(timeout=10.0) as http:
        resp = await http.get("https://official-joke-api.appspot.com/random_joke")
        resp.raise_for_status()
        data = resp.json()
    await react_task
    await msg.reply_text(f"*{data['setup']}*\n\n{data['punchline']}")


@wa.on_message(filters.text)
async def chat(_: WhatsApp, msg: types.Message) -> None:
    # Stand-in for an LLM / DB call. Awaiting here doesn't block the event loop.
    await asyncio.sleep(0.1)
    await msg.reply_text(f"You said: {msg.text}")


@wa.on_message
async def wave(_: WhatsApp, msg: types.Message) -> None:
    await msg.react("👋")
