# ruff: noqa: T201
"""
Account Verification (OTP) Bot
================================
Feature focus: `pywa` message templates — sending a pre-approved *authentication* template to
deliver a one-time password, then verifying the user's reply.

Run `setup_template.py` once (and wait for Meta's approval) before starting this bot.
"""

import os
import random

import dotenv

from pywa_async import WhatsApp, filters, types
from pywa_async.types import TemplateStatusUpdate
from pywa_async.types.templates import (
    AuthenticationBody,
    CopyCodeOTPButton,
    TemplateLanguage,
    TemplateStatus,
)
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
    waba_id=os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"],
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
)

TEMPLATE_NAME = os.getenv("OTP_TEMPLATE_NAME", "account_verification_code")

VERIFIED_USERS: set[str] = set()  # bsuid. Swap for a real user store in production.


@wa.on_message(filters.command("verify", ignore_case=True))
async def send_otp(_: WhatsApp, msg: types.Message):
    if msg.from_user.bsuid in VERIFIED_USERS:
        await msg.reply("You're already verified ✅")
        return

    code = f"{random.randint(0, 999999):06d}"
    sent = await wa.send_template(
        to=msg.from_user.bsuid,
        name=TEMPLATE_NAME,
        language=TemplateLanguage.ENGLISH_US,
        params=[
            AuthenticationBody.params(otp=code),
            CopyCodeOTPButton.params(otp=code),
        ],
    )

    try:
        reply = await sent.wait_for_reply(
            filters=filters.text,
            cancelers=filters.command("cancel", ignore_case=True),
            timeout=300,
        )
    except types.ListenerTimeout:
        await msg.reply("⌛ Verification timed out. Send /verify to get a new code.")
        return
    except types.ListenerCanceled:
        await msg.reply("Verification canceled.")
        return

    if reply.text.strip() == code:
        VERIFIED_USERS.add(msg.from_user.bsuid)
        await reply.react("✅")
        await reply.reply("You're verified! Welcome aboard 🎉")
    else:
        await reply.reply("❌ That code doesn't match. Send /verify to get a new one.")


@wa.on_template_status_update
async def on_template_status(_: WhatsApp, update: TemplateStatusUpdate):
    if update.new_status == TemplateStatus.APPROVED:
        print(f"Template {update.template_id} approved — the bot can now send OTPs!")
    elif update.new_status == TemplateStatus.REJECTED:
        print(f"Template {update.template_id} rejected: {update.reason}")


# Run with: pywa dev
