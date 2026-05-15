"""
05 — Templates: create + send

Templates are pre-approved message payloads. They're how you can message a user
outside the 24-hour service window (e.g. promos, reminders, OTPs).

This script:
1. Creates a marketing template with a header, body, footer and 3 buttons.
2. Sends it to a recipient with per-call parameter values.

It does NOT need a webhook — it's a plain script. Run it once and then
re-run with the `send` argument to send the template:

    python main.py create   # creates the template (one-time; Meta reviews it)
    python main.py send     # sends the template to WA_TEST_RECIPIENT
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

from pywa import WhatsApp
from pywa.types.templates import (
    BodyText,
    Buttons,
    FooterText,
    HeaderText,
    ParamFormat,
    PhoneNumberButton,
    QuickReplyButton,
    Template,
    TemplateCategory,
    TemplateLanguage,
    URLButton,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

TEMPLATE_NAME = "buy_new_iphone_x"

wa = WhatsApp(
    phone_id=os.environ["WA_PHONE_ID"],
    token=os.environ["WA_TOKEN"],
    business_account_id=os.environ["WA_BUSINESS_ACCOUNT_ID"],
)


def create() -> None:
    """Create-and-publish the template. Meta then reviews it (usually < 1h)."""
    ht = HeaderText("The New iPhone {{iphone_num}} is here!", iphone_num=15)
    bt = BodyText(
        "Buy now and use the code {{code}} to get {{per}}% off!",
        code="WA_IPHONE_15",
        per=15,
    )
    url = URLButton(
        text="Buy Now", url="https://example.com/shop/{{1}}", example="iphone15"
    )
    qr_marketing = QuickReplyButton(text="Unsubscribe from marketing messages")
    qr_all = QuickReplyButton(text="Unsubscribe from all messages")

    result = wa.create_template(
        template=Template(
            name=TEMPLATE_NAME,
            category=TemplateCategory.MARKETING,
            language=TemplateLanguage.ENGLISH_US,
            parameter_format=ParamFormat.NAMED,
            components=[
                ht,
                bt,
                FooterText(text="Powered by PyWa"),
                Buttons(
                    buttons=[
                        url,
                        PhoneNumberButton(text="Call Us", phone_number="1234567890"),
                        qr_marketing,
                        qr_all,
                    ]
                ),
            ],
        ),
    )
    logging.info("Template submitted. id=%s status=%s", result.id, result.status)
    logging.info("Wait until status is APPROVED, then run: python main.py send")


def send() -> None:
    """Send the (approved) template. Field values are filled per-call."""
    recipient = os.environ["WA_TEST_RECIPIENT"]

    # Rebuild references so we can call `.params(...)` for this specific send.
    ht = HeaderText("The New iPhone {{iphone_num}} is here!", iphone_num=15)
    bt = BodyText(
        "Buy now and use the code {{code}} to get {{per}}% off!",
        code="WA_IPHONE_15",
        per=15,
    )
    url = URLButton(
        text="Buy Now", url="https://example.com/shop/{{1}}", example="iphone15"
    )
    qr_marketing = QuickReplyButton(text="Unsubscribe from marketing messages")
    qr_all = QuickReplyButton(text="Unsubscribe from all messages")

    sent = wa.send_template(
        to=recipient,
        name=TEMPLATE_NAME,
        language=TemplateLanguage.ENGLISH_US,
        params=[
            ht.params(iphone_num=30),
            bt.params(code="WA_IPHONE_30", per=30),
            url.params(url_variable="iphone30", index=0),
            qr_marketing.params(callback_data="unsub_marketing", index=1),
            qr_all.params(callback_data="unsub_all", index=2),
        ],
    )
    logging.info("Template sent. message_id=%s", sent.id)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "send"
    if action == "create":
        create()
    elif action == "send":
        send()
    else:
        print("Usage: python main.py {create|send}", file=sys.stderr)
        sys.exit(2)
