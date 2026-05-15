"""
04 — Flow: newsletter signup

A WhatsApp Flow is a multi-screen form rendered natively inside the chat.
This example:

1. Builds a single-screen Flow (`FlowJSON`).
2. Creates and publishes it on Meta's servers (once, on startup).
3. Sends it via a `FlowButton` when a user types "subscribe".
4. Handles the submitted data in `on_flow_completion`.

Flows require **end-to-end encryption** between Meta and your server.
You need an RSA key pair — see ../README.md for setup, or the README in this folder.

Run:
    cp ../.env.example .env  # fill in WA_BUSINESS_ACCOUNT_ID, WA_FLOW_PRIVATE_KEY_PATH, etc.
    fastapi dev main.py
"""

from __future__ import annotations

import contextlib
import logging
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI

from pywa import WhatsApp, filters, types
from pywa.types.flows import (
    CompleteAction,
    FlowCategory,
    FlowJSON,
    Footer,
    InputType,
    Layout,
    Screen,
    TextHeading,
    TextInput,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

FLOW_NAME = "subscribe_to_newsletter"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_flow_exists()
    yield


fastapi_app = FastAPI(lifespan=lifespan)

wa = WhatsApp(
    phone_id=os.environ["WA_PHONE_ID"],
    token=os.environ["WA_TOKEN"],
    business_account_id=os.environ["WA_BUSINESS_ACCOUNT_ID"],
    server=fastapi_app,
    callback_url=os.environ["WA_CALLBACK_URL"],
    verify_token=os.environ["WA_VERIFY_TOKEN"],
    app_id=int(os.environ["WA_APP_ID"]),
    app_secret=os.environ["WA_APP_SECRET"],
    business_private_key=pathlib.Path(
        os.environ["WA_FLOW_PRIVATE_KEY_PATH"]
    ).read_text(),
    business_private_key_password=os.environ.get("WA_FLOW_PRIVATE_KEY_PASSWORD"),
)


def build_flow_json() -> FlowJSON:
    """Single screen: ask for name + email, submit closes the flow."""
    name = TextInput(name="name", label="Name", input_type=InputType.TEXT, required=False)
    email = TextInput(name="email", label="Email", input_type=InputType.EMAIL, required=True)
    return FlowJSON(
        screens=[
            Screen(
                id="NEWSLETTER",
                title="PyWa Newsletter",
                terminal=True,
                layout=Layout(
                    children=[
                        TextHeading(text="Subscribe to our newsletter"),
                        name,
                        email,
                        Footer(
                            label="Subscribe",
                            on_click_action=CompleteAction(
                                payload={"name": name.ref, "email": email.ref}
                            ),
                        ),
                    ]
                ),
            )
        ]
    )


# Create-or-update the flow on Meta once at startup. Called from the lifespan above.
def ensure_flow_exists() -> None:
    existing = {f.name: f for f in wa.get_flows()}
    if FLOW_NAME not in existing:
        wa.create_flow(
            name=FLOW_NAME,
            categories=[FlowCategory.SIGN_UP, FlowCategory.OTHER],
            flow_json=build_flow_json(),
            publish=True,
        )
        logging.info("Created flow %r.", FLOW_NAME)
    else:
        logging.info("Flow %r already exists (id=%s).", FLOW_NAME, existing[FLOW_NAME].id)


@wa.on_message(filters.matches("subscribe", "/subscribe", ignore_case=True))
def offer_flow(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text(
        text="Want our newsletter? Tap below.",
        buttons=types.FlowButton(
            title="Subscribe",
            flow_name=FLOW_NAME,
        ),
    )


@wa.on_flow_completion
def on_subscribed(_: WhatsApp, flow: types.FlowCompletion) -> None:
    name = flow.response.get("name") or "friend"
    email = flow.response["email"]
    flow.reply_text(
        text=f"Thanks, {name}! We'll send updates to {email}. 📬",
        buttons=[types.Button(title="Unsubscribe", callback_data="unsubscribe")],
    )


@wa.on_callback_button(filters.matches("unsubscribe"))
def on_unsubscribe(_: WhatsApp, btn: types.CallbackButton) -> None:
    # Real implementation would remove the user from your DB / email provider.
    btn.reply_text("You've been unsubscribed.")
