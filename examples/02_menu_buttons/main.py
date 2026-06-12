"""
02 — Menu with buttons and section lists

Shows the three flavors of interactive messages in PyWa:
- Quick-reply buttons (max 3).
- Section list (a longer scrollable menu).
- Typed callback data via `CallbackData` dataclasses.

Run:
    cp ../.env.example .env  # then edit the values
    fastapi dev main.py
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from fastapi import FastAPI

from pywa import WhatsApp, filters, types

load_dotenv()
logging.basicConfig(level=logging.INFO)


# A typed callback payload. PyWa serializes this to a short string so it fits in WhatsApp's
# 200-char button payload limit, and automatically rehydrates it in the handler.
@dataclass(frozen=True, slots=True)
class Action(types.CallbackData):
    name: str
    quantity: int = 1


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


@wa.on_message(filters.matches("menu", "/menu", ignore_case=True))
def show_menu(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text(
        text="What would you like to order?",
        header="🍕 PyWa Pizzeria",
        footer="Tap an option below.",
        buttons=[
            types.Button(title="🍕 Pizza", callback_data=Action(name="pizza")),
            types.Button(title="🍔 Burger", callback_data=Action(name="burger")),
            types.Button(title="📜 Full menu", callback_data="full_menu"),
        ],
    )


@wa.on_callback_button(factory=Action)
def on_order_click(_: WhatsApp, btn: types.CallbackButton[Action]) -> None:
    msg = f"Added {btn.data.quantity} × {btn.data.name} to your cart."
    btn.reply_text(msg)


# A scrollable list for the longer menu.
@wa.on_callback_button(filters.matches("full_menu"))
def on_full_menu(_: WhatsApp, btn: types.CallbackButton) -> None:
    btn.reply_text(
        text="Pick a dish:",
        header="🍽️ Full menu",
        buttons=types.SectionList(
            button_title="Browse menu",
            sections=[
                types.Section(
                    title="Mains",
                    rows=[
                        types.SectionRow(
                            title="Margherita pizza",
                            callback_data=Action(name="margherita"),
                            description="Tomato, mozzarella, basil",
                        ),
                        types.SectionRow(
                            title="Pepperoni pizza",
                            callback_data=Action(name="pepperoni"),
                            description="Spicy pepperoni, cheese",
                        ),
                        types.SectionRow(
                            title="Veggie burger",
                            callback_data=Action(name="veggie_burger"),
                            description="Plant-based patty",
                        ),
                    ],
                ),
                types.Section(
                    title="Drinks",
                    rows=[
                        types.SectionRow(
                            title="Soda",
                            callback_data=Action(name="soda"),
                        ),
                        types.SectionRow(
                            title="Water",
                            callback_data=Action(name="water"),
                        ),
                    ],
                ),
            ],
        ),
    )


# `CallbackSelection` is what section-list taps deliver. The `factory` rehydrates `Action`.
@wa.on_callback_selection(factory=Action)
def on_dish_pick(_: WhatsApp, sel: types.CallbackSelection[Action]) -> None:
    sel.reply_text(f"Great choice! Adding {sel.data.name} to your cart.")


# Friendly fallback for everything else.
@wa.on_message
def fallback(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text('Type "menu" to see what we have today.')
