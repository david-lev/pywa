"""
WhatsApp-Native Admin Console Bot
===================================
Feature focus: the `pywa.client.WhatsApp` business-management API — reading/updating your
business profile and commerce settings, and checking phone number health, all driven by chat
commands from an admin's own WhatsApp number. No separate admin dashboard required.
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

ADMIN_NUMBERS = {
    n.strip() for n in os.getenv("ADMIN_NUMBERS", "").split(",") if n.strip()
}

is_admin = filters.from_users(*ADMIN_NUMBERS)


@wa.on_message(~is_admin)
async def deny_non_admins(_: WhatsApp, msg: types.Message):
    await msg.reply("This number is not authorized to use the admin console.")


@wa.on_message(filters.command("profile", ignore_case=True) & is_admin)
async def show_profile(_: WhatsApp, msg: types.Message):
    profile = await wa.get_business_profile()
    await msg.reply(
        "*Business profile*\n"
        f"About: {profile.about or '—'}\n"
        f"Description: {profile.description or '—'}\n"
        f"Email: {profile.email or '—'}\n"
        f"Address: {profile.address or '—'}\n"
        f"Websites: {', '.join(profile.websites) if profile.websites else '—'}"
    )


@wa.on_message(filters.command("set_about", ignore_case=True) & is_admin)
async def set_about(_: WhatsApp, msg: types.Message):
    text = msg.text.partition(" ")[2]
    if not text:
        await msg.reply("Usage: /set_about <text>")
        return
    await wa.update_business_profile(about=text)
    await msg.reply("✅ Updated the 'about' text.")


@wa.on_message(filters.command("set_description", ignore_case=True) & is_admin)
async def set_description(_: WhatsApp, msg: types.Message):
    text = msg.text.partition(" ")[2]
    if not text:
        await msg.reply("Usage: /set_description <text>")
        return
    await wa.update_business_profile(description=text)
    await msg.reply("✅ Updated the business description.")


@wa.on_message(filters.command("commerce", ignore_case=True) & is_admin)
async def show_commerce(_: WhatsApp, msg: types.Message):
    settings = await wa.get_commerce_settings()
    await msg.reply(
        "*Commerce settings*\n"
        f"Catalog visible: {settings.is_catalog_visible}\n"
        f"Cart enabled: {settings.is_cart_enabled}"
    )


@wa.on_message(filters.regex(r"(?i)^/(cart|catalog)\s+(on|off)$") & is_admin)
async def toggle_commerce(_: WhatsApp, msg: types.Message):
    setting, value = (
        msg.text.split()[0].lstrip("/").lower(),
        msg.text.split()[1].lower(),
    )
    enabled = value == "on"
    if setting == "cart":
        await wa.update_commerce_settings(is_cart_enabled=enabled)
    else:
        await wa.update_commerce_settings(is_catalog_visible=enabled)
    await msg.reply(
        f"✅ {setting.capitalize()} is now {'enabled' if enabled else 'disabled'}."
    )


@wa.on_message(filters.command("number_info", ignore_case=True) & is_admin)
async def number_info(_: WhatsApp, msg: types.Message):
    number = await wa.get_business_phone_number()
    await msg.reply(
        "*Phone number health*\n"
        f"Display number: {number.display_phone_number}\n"
        f"Verified name: {number.verified_name}\n"
        f"Status: {number.status}\n"
        f"Quality rating: {number.quality_rating}\n"
        f"Messaging limit tier: {number.messaging_limit_tier}"
    )


@wa.on_message(filters.command("help", "start", ignore_case=True) & is_admin)
async def help_(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "*Admin console*\n"
        "/profile — show the business profile\n"
        "/set_about <text> — update the 'about' text\n"
        "/set_description <text> — update the description\n"
        "/commerce — show commerce (catalog/cart) settings\n"
        "/cart on|off — toggle the cart\n"
        "/catalog on|off — toggle catalog visibility\n"
        "/number_info — show phone number health & quality rating"
    )


# Run with: pywa dev
