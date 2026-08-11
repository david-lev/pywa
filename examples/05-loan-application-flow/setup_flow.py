"""
One-time setup script.

Creates the WhatsApp Flow used by `main.py`, and points it at your webhook endpoint. Run this
once:

    python3 setup_flow.py

Then copy the printed flow ID into `LOAN_FLOW_ID` in your `.env`.
"""

import asyncio
import os
import pathlib

import dotenv
from flow_json import loan_application_flow

from pywa_async import WhatsApp
from pywa_async.types import FlowCategory

dotenv.load_dotenv()


async def main():
    wa = WhatsApp(
        token=os.environ["WHATSAPP_TOKEN"],
        waba_id=os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"],
    )

    # Upload your business public key once (required for encrypted flow data exchange).
    # See README.md for how to generate the private.pem / public.pem pair.
    key_path = pathlib.Path(os.environ["BUSINESS_PUBLIC_KEY_PATH"])
    await wa.set_business_public_key(await asyncio.to_thread(key_path.read_text))

    created = await wa.create_flow(
        name="Loan Application",
        categories=[FlowCategory.LEAD_GENERATION],
        flow_json=loan_application_flow,
    )
    print(f"Flow created: id={created.id}")

    await wa.update_flow_metadata(
        flow_id=created.id,
        endpoint_uri=f"{os.environ['CALLBACK_URL']}/flows/loan-application",
    )
    print(f"Set LOAN_FLOW_ID={created.id} in your .env, then run: pywa dev")
    print(
        "The flow starts in DRAFT mode (main.py already sends it with mode=FlowStatus.DRAFT so "
        "you can test it right away). Publish it from WhatsApp Manager when you're ready to go live, "
        "and switch main.py to mode=FlowStatus.PUBLISHED."
    )


if __name__ == "__main__":
    asyncio.run(main())
