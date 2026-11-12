"""
Voice Call-Back Bot
=====================
Feature focus: the WhatsApp Calling API (`pywa.types.calls`) — requesting call permission,
initiating/accepting calls, and reacting to the full call lifecycle (ringing, answered, rejected,
terminated).

⚠️ pywa transports call *signaling* (permissions, SDP offers/answers, lifecycle events) — it does
not negotiate or carry audio itself. A real deployment still needs a WebRTC/VoIP media stack to
produce actual SDP answers and handle the RTP audio stream. This example uses a static placeholder
SDP (`answer.sdp`) so you can see the full call flow without that extra infrastructure — see
README.md for what a production setup additionally needs.
"""

import os
import pathlib

import dotenv

from pywa_async import WhatsApp, filters, types
from pywa_async.types.calls import CallPermissionStatus, SessionDescription

dotenv.load_dotenv()

wa = WhatsApp(
    phone_id=os.environ["PYWA_PHONE_ID"],
    token=os.environ["PYWA_TOKEN"],
    app_id=os.environ.get("PYWA_APP_ID"),
    app_secret=os.environ["PYWA_APP_SECRET"],
)

STAFF_NUMBER = os.getenv("STAFF_NUMBER")

_PLACEHOLDER_SDP = SessionDescription(
    sdp_type="answer",
    sdp=(pathlib.Path(__file__).parent / "answer.sdp").read_text(),
)


async def _call_back(to: str):
    call = await wa.initiate_call(to=to, sdp=_PLACEHOLDER_SDP)
    wa.logger.info("Calling %s back (call id: %s)", to, call.id)


@wa.on_message(filters.command("call_me", ignore_case=True))
async def request_callback(_: WhatsApp, msg: types.Message):
    permissions = await wa.get_call_permissions(from_user=msg.from_user.bsuid)
    if permissions.permission.status == CallPermissionStatus.NO_PERMISSION:
        await msg.reply(
            text="We'd like to call you back about your request — is that okay?",
            buttons=types.CallPermissionRequestButton(),
        )
    else:
        await msg.reply("Calling you now! 📞")
        await _call_back(msg.from_user.bsuid)


@wa.on_call_permission_update(filters.call_permission_accepted)
async def on_permission_granted(_: WhatsApp, update: types.CallPermissionUpdate):
    await update.reply("Great, calling you now! 📞")
    await _call_back(update.from_user.bsuid)


@wa.on_call_permission_update(filters.call_permission_rejected)
async def on_permission_denied(_: WhatsApp, update: types.CallPermissionUpdate):
    await update.reply("No problem — you can text us here anytime instead.")


@wa.on_call_connect(filters.incoming_call)
async def on_incoming_call(_: WhatsApp, call: types.CallConnect):
    """
    A customer is calling the business directly. Pre-accepting first (recommended by Meta) reduces
    audio clipping once we `accept` right after — see the docstring at the top of this file about
    why both use a placeholder SDP here.
    """
    await call.pre_accept(sdp=_PLACEHOLDER_SDP)
    await call.accept(sdp=_PLACEHOLDER_SDP)
    wa.logger.info("Answered an incoming call from %s", call.from_user.bsuid)


@wa.on_call_status(filters.call_ringing)
async def on_ringing(_: WhatsApp, status: types.CallStatus):
    wa.logger.info("Call to %s is ringing…", status.from_user.bsuid)


@wa.on_call_status(filters.call_answered)
async def on_answered(_: WhatsApp, status: types.CallStatus):
    wa.logger.info("Call to %s was answered!", status.from_user.bsuid)


@wa.on_call_status(filters.call_rejected)
async def on_call_status_rejected(_: WhatsApp, status: types.CallStatus):
    wa.logger.warning("Call to %s was rejected.", status.from_user.bsuid)
    if STAFF_NUMBER:
        await wa.send_message(
            to=STAFF_NUMBER, text=f"Callback to {status.from_user.bsuid} was rejected."
        )


@wa.on_call_terminate
async def on_call_terminate(_: WhatsApp, call: types.CallTerminate):
    wa.logger.info(
        "Call with %s ended: status=%s, duration=%ss",
        call.from_user.bsuid,
        call.status,
        call.duration,
    )


# Run with: pywa dev
