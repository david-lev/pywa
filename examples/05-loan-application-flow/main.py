"""
Loan Application Flow Bot
===========================
Feature focus: WhatsApp Flows (`pywa.types.flows`) — a rich, multi-screen form collected entirely
inside WhatsApp, with the server validating each step and computing a result before submission.

Run `setup_flow.py` once before starting this bot (see README.md).
"""

import os

import dotenv
from flow_json import loan_details_screen, personal_info_screen, review_screen

from pywa_async import WhatsApp, filters, types
from pywa_async.types import (
    FlowActionType,
    FlowButton,
    FlowCompletion,
    FlowRequest,
    FlowResponse,
    FlowStatus,
)
from pywa_async.utils import start_ngrok_tunnel

dotenv.load_dotenv()

callback_url = os.getenv("CALLBACK_URL")
if not callback_url:
    callback_url = start_ngrok_tunnel(auth_token=os.environ["NGROK_AUTH_TOKEN"])

with open(os.environ["BUSINESS_PRIVATE_KEY_PATH"], encoding="utf-8") as f:
    business_private_key = f.read()

wa = WhatsApp(
    phone_id=os.environ["WHATSAPP_PHONE_ID"],
    token=os.environ["WHATSAPP_TOKEN"],
    app_id=os.environ["WHATSAPP_APP_ID"],
    app_secret=os.environ["WHATSAPP_APP_SECRET"],
    waba_id=os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"],
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
    business_private_key=business_private_key,
    business_private_key_password=os.getenv("BUSINESS_PRIVATE_KEY_PASSWORD"),
)

LOAN_FLOW_ID = os.environ["LOAN_FLOW_ID"]

# flow_token -> partial application data collected across screens. Swap for a real DB in production.
APPLICATIONS: dict[str, dict] = {}


@wa.on_message(filters.command("apply", ignore_case=True))
async def start_application(_: WhatsApp, msg: types.Message):
    await msg.reply(
        text="Ready to apply for a loan? Tap below to get started.",
        buttons=FlowButton(
            title="Start Application",
            flow_id=LOAN_FLOW_ID,
            flow_token=msg.from_user.bsuid,
            # The flow starts in DRAFT mode so you can test it immediately after setup_flow.py.
            # Switch to FlowStatus.PUBLISHED once you've published the flow in WhatsApp Manager.
            mode=FlowStatus.DRAFT,
            flow_action_type=FlowActionType.NAVIGATE,
            flow_action_screen="PERSONAL_INFO",
        ),
    )


@wa.on_flow_request(endpoint="/flows/loan-application")
def handle_loan_flow(_: WhatsApp, req: FlowRequest) -> FlowResponse:
    raise NotImplementedError(req)


@handle_loan_flow.on_init
def on_init(_: WhatsApp, req: FlowRequest) -> FlowResponse:
    APPLICATIONS[req.flow_token] = {}
    return req.respond(screen=personal_info_screen)


@handle_loan_flow.on_data_exchange(screen=personal_info_screen)
def on_personal_info(_: WhatsApp, req: FlowRequest) -> FlowResponse:
    if "@" not in req.data["email"]:
        return req.respond(
            screen=personal_info_screen,
            error_message="Please enter a valid email address.",
        )
    APPLICATIONS.setdefault(req.flow_token, {}).update(req.data)
    return req.respond(screen=loan_details_screen)


@handle_loan_flow.on_data_exchange(screen=loan_details_screen)
def on_loan_details(_: WhatsApp, req: FlowRequest) -> FlowResponse:
    try:
        amount = float(req.data["loan_amount"])
    except ValueError:
        return req.respond(
            screen=loan_details_screen, error_message="Enter a valid loan amount."
        )
    if not (0 < amount <= 100_000):
        return req.respond(
            screen=loan_details_screen,
            error_message="Loan amount must be between $1 and $100,000.",
        )

    application = APPLICATIONS.setdefault(req.flow_token, {})
    application.update(req.data)
    # Naive 24-month, interest-free estimate — replace with your real underwriting logic.
    monthly_payment = round(amount / 24, 2)
    summary = (
        f"Applicant: {application.get('full_name', '')}\n"
        f"Loan amount: ${amount:,.2f}\n"
        f"Purpose: {application.get('loan_purpose', '')}\n"
        f"Estimated monthly payment (24 mo): ${monthly_payment:,.2f}"
    )
    return req.respond(screen=review_screen, data={"summary": summary})


@wa.on_flow_completion
async def on_flow_completion(_: WhatsApp, flow: FlowCompletion):
    application = APPLICATIONS.pop(flow.token, {})
    await flow.reply(
        f"🎉 Thanks {application.get('full_name', 'there')}! Your loan application has been "
        "submitted and a loan officer will follow up within 1-2 business days."
    )


# Run with: pywa dev
