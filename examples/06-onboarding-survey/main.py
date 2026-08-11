"""
New Customer Onboarding Survey Bot
====================================
Feature focus: `pywa` listeners — pausing execution inline to wait for the user's next reply,
instead of registering a separate handler for every step of a conversation.
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

# bsuid -> collected answers. Swap for a real database/CRM in production.
SURVEY_RESPONSES: dict[str, dict] = {}

CANCEL_BUTTON = types.Button(title="Cancel", callback_data="onboarding:cancel")
cancel_filter = filters.callback_button & filters.matches("onboarding:cancel")


@wa.on_message(filters.command("start", "hi", ignore_case=True))
async def start_onboarding(_: WhatsApp, msg: types.Message):
    answers: dict = {}
    try:
        sent = await msg.reply(
            "👋 Welcome! Let's get you set up — what's your name?",
            buttons=[CANCEL_BUTTON],
        )
        name_reply = await sent.wait_for_reply(
            filters=filters.text, cancelers=cancel_filter, timeout=120
        )
        answers["name"] = name_reply.text

        sent = await name_reply.reply(
            f"Nice to meet you, {answers['name']}! What will you use us for?",
            buttons=[
                types.Button(title="Personal", callback_data="usecase:personal"),
                types.Button(title="Business", callback_data="usecase:business"),
                CANCEL_BUTTON,
            ],
        )
        usecase_reply = await sent.wait_for_click(cancelers=cancel_filter, timeout=120)
        answers["use_case"] = usecase_reply.data.split(":")[1]

        sent = await usecase_reply.reply(
            "How big is your team?",
            buttons=types.SectionList(
                button_title="Choose team size",
                sections=[
                    types.Section(
                        title="Team size",
                        rows=[
                            types.SectionRow(
                                title="Just me", callback_data="size:solo"
                            ),
                            types.SectionRow(title="2-10", callback_data="size:small"),
                            types.SectionRow(
                                title="11-50", callback_data="size:medium"
                            ),
                            types.SectionRow(title="50+", callback_data="size:large"),
                        ],
                    )
                ],
            ),
        )
        size_reply = await sent.wait_for_selection(cancelers=cancel_filter, timeout=120)
        answers["team_size"] = size_reply.data.split(":")[1]

        # A manual retry loop: the listener just waits for *any* text reply, and we validate
        # it ourselves so we can re-prompt without falling back to a registered handler.
        sent = await size_reply.reply("Last thing — what's your email address?")
        while True:
            email_reply = await sent.wait_for_reply(
                filters=filters.text, cancelers=cancel_filter, timeout=120
            )
            if "@" in email_reply.text and "." in email_reply.text.split("@")[-1]:
                answers["email"] = email_reply.text
                break
            sent = await email_reply.reply(
                "That doesn't look like a valid email — try again?"
            )

    except types.ListenerCanceled:
        await msg.reply("No problem — you can restart onboarding anytime with /start.")
        return
    except types.ListenerTimeout:
        await msg.reply(
            "⌛ You took a while to respond — send /start whenever you're ready."
        )
        return

    SURVEY_RESPONSES[msg.from_user.bsuid] = answers
    await email_reply.reply(
        f"All set, {answers['name']}! 🎉\n"
        f"Use case: {answers['use_case']} · Team size: {answers['team_size']}\n"
        f"Email: {answers['email']}\n\n"
        "We'll tailor your experience accordingly."
    )


# Run with: pywa dev
