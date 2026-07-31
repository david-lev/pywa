"""
Quick-Serve Restaurant Ordering Bot
====================================
Feature focus: `pywa.types` keyboard & media — interactive buttons, section lists and rich media
replies used together to build a browse → add-to-cart → checkout flow entirely inside WhatsApp.
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

TRACK_ORDER_URL = os.getenv("TRACK_ORDER_URL", "https://example.com/track-order")

# A tiny in-memory "menu" and "cart". Swap these for a real database in production.
MENU = {
    "bruschetta": {
        "name": "Bruschetta",
        "price": 6.5,
        "desc": "Grilled bread, tomato & basil",
        "category": "🥗 Starters",
    },
    "soup": {
        "name": "Soup of the Day",
        "price": 5.0,
        "desc": "Ask your server for today's flavor",
        "category": "🥗 Starters",
    },
    "margherita": {
        "name": "Margherita Pizza",
        "price": 12.0,
        "desc": "Tomato, mozzarella & basil",
        "category": "🍝 Mains",
        "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002",
    },
    "carbonara": {
        "name": "Spaghetti Carbonara",
        "price": 13.5,
        "desc": "Egg, pancetta & pecorino",
        "category": "🍝 Mains",
        "image": "https://images.unsplash.com/photo-1612874742237-6526221588e3",
    },
    "tiramisu": {
        "name": "Tiramisu",
        "price": 6.0,
        "desc": "Coffee-soaked ladyfingers & mascarpone",
        "category": "🍰 Desserts",
    },
}

CARTS: dict[str, list[str]] = {}  # bsuid -> list of item ids


def cart_summary(bsuid: str) -> str:
    items = CARTS.get(bsuid, [])
    if not items:
        return "Your cart is empty."
    lines = [
        f"• {MENU[item_id]['name']} — ${MENU[item_id]['price']:.2f}"
        for item_id in items
    ]
    total = sum(MENU[item_id]["price"] for item_id in items)
    return "\n".join(lines) + f"\n\n*Total: ${total:.2f}*"


@wa.on_message(filters.command("start", "menu", "hi", ignore_case=True))
async def show_menu(_: WhatsApp, msg: types.Message):
    sections: dict[str, list[types.SectionRow]] = {}
    for item_id, item in MENU.items():
        sections.setdefault(item["category"], []).append(
            types.SectionRow(
                title=item["name"],
                callback_data=f"item:{item_id}",
                description=f"${item['price']:.2f} — {item['desc']}",
            )
        )
    await msg.reply(
        text="Welcome to *Quick-Serve*! 🍽️ Browse our menu and tap an item to add it to your cart.",
        buttons=types.SectionList(
            button_title="📋 View Menu",
            sections=[
                types.Section(title=category, rows=rows)
                for category, rows in sections.items()
            ],
        ),
    )


@wa.on_callback_selection(filters.startswith("item:"))
async def show_item(_: WhatsApp, sel: types.CallbackSelection):
    item_id = sel.data.split(":")[1]
    item = MENU[item_id]
    caption = f"*{item['name']}* — ${item['price']:.2f}\n{item['desc']}"
    buttons = [
        types.Button(title="➕ Add to cart", callback_data=f"cart:add:{item_id}"),
        types.Button(title="🛒 View cart", callback_data="cart:view"),
    ]
    if image := item.get("image"):
        await sel.reply_image(image=image, caption=caption, buttons=buttons)
    else:
        await sel.reply(text=caption, buttons=buttons)


@wa.on_callback_button(filters.startswith("cart:add:"))
async def add_to_cart(_: WhatsApp, clb: types.CallbackButton):
    item_id = clb.data.split(":")[2]
    CARTS.setdefault(clb.from_user.bsuid, []).append(item_id)
    await clb.react("✅")
    await clb.reply(
        text=f"Added *{MENU[item_id]['name']}* to your cart!\n\n{cart_summary(clb.from_user.bsuid)}",
        buttons=[
            types.Button(title="🛒 View cart", callback_data="cart:view"),
            types.Button(title="✅ Checkout", callback_data="cart:checkout"),
        ],
    )


@wa.on_callback_button(filters.matches("cart:view"))
async def view_cart(_: WhatsApp, clb: types.CallbackButton):
    await clb.reply(
        text=cart_summary(clb.from_user.bsuid),
        buttons=[
            types.Button(title="✅ Checkout", callback_data="cart:checkout"),
            types.Button(title="🗑️ Clear cart", callback_data="cart:clear"),
        ],
    )


@wa.on_callback_button(filters.matches("cart:clear"))
async def clear_cart(_: WhatsApp, clb: types.CallbackButton):
    CARTS.pop(clb.from_user.bsuid, None)
    await clb.reply("🗑️ Your cart has been cleared.")


@wa.on_callback_button(filters.matches("cart:checkout"))
async def checkout(_: WhatsApp, clb: types.CallbackButton):
    items = CARTS.pop(clb.from_user.bsuid, [])
    if not items:
        await clb.reply("Your cart is empty — send /menu to start ordering.")
        return
    total = sum(MENU[item_id]["price"] for item_id in items)
    await clb.reply(
        text=(
            "🎉 Order confirmed! Estimated prep time: 20 minutes.\n"
            f"Total charged: ${total:.2f}\n\n"
            "Thanks for ordering from Quick-Serve!"
        ),
        buttons=types.URLButton(title="🔗 Track your order", url=TRACK_ORDER_URL),
    )


# Run with: pywa dev
