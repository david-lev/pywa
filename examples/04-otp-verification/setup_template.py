"""
One-time setup script.

Creates the WhatsApp *authentication* template used by `main.py` to send one-time
verification codes. Run this once:

    python3 setup_template.py

...then wait for Meta to approve the template (check the WhatsApp Manager dashboard, or your
Meta App's "Message Templates" tab) before running the bot in `main.py`.
"""

import asyncio
import os

import dotenv

from pywa_async import WhatsApp
from pywa_async.types.templates import (
    AuthenticationBody,
    AuthenticationFooter,
    Buttons,
    CopyCodeOTPButton,
    Template,
    TemplateCategory,
    TemplateLanguage,
)

dotenv.load_dotenv()

TEMPLATE_NAME = os.getenv("OTP_TEMPLATE_NAME", "account_verification_code")

auth_template = Template(
    name=TEMPLATE_NAME,
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.AUTHENTICATION,
    components=[
        AuthenticationBody(add_security_recommendation=True),
        AuthenticationFooter(code_expiration_minutes=10),
        Buttons(buttons=[CopyCodeOTPButton()]),
    ],
)


async def main():
    wa = WhatsApp(
        token=os.environ["WHATSAPP_TOKEN"],
        waba_id=os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"],
    )
    created = await wa.create_template(auth_template)
    print(
        f"Template '{TEMPLATE_NAME}' created: id={created.id} status={created.status}"
    )
    print("Wait for it to be approved before running main.py")


if __name__ == "__main__":
    asyncio.run(main())
