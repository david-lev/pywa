from __future__ import annotations

from typing import TYPE_CHECKING

"""This module contains types related to WhatsApp calls, including call connection, termination, and status updates."""


from pywa.types.calls import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.calls import (
    CallConnect as _CallConnect,
    CallTerminate as _CallTerminate,
    CallStatus as _CallStatus,
    CallPermissionUpdate as _CallPermissionUpdate,
)

import dataclasses

from .base_update import BaseUserUpdateAsync  # noqa
from .callback import CallbackData
from .others import SuccessResult

if TYPE_CHECKING:
    from .sent_update import InitiatedCall
    from ..client import WhatsApp as WhatsAppAsync


class _CallShortcutsAsync:
    """Base class for async call actions."""

    id: str
    _client: WhatsAppAsync
    sender: str
    recipient: str

    async def pre_accept(self, *, sdp: SessionDescription) -> SuccessResult:
        """
        Pre-accept the call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#pre-accept-call>`_.

        In essence, when you pre-accept an inbound call, you are allowing the calling media connection to be established before attempting to send call media through the connection.

        When you then call the accept call endpoint, media begins flowing immediately since the connection has already been established

        Pre-accepting calls is recommended because it facilitates faster connection times and avoids `audio clipping issues <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/troubleshooting#audio-clipping-issue-and-solution>`_.

        There is about 30 to 60 seconds after the Call Connect webhook is sent for the business to accept the phone call. If the business does not respond, the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Args:
            sdp: Contains the session description protocol (SDP) type and description language.

        Returns:
            Whether the call was pre-accepted.
        """
        return await self._client.pre_accept_call(call_id=self.id, sdp=sdp)

    async def accept(
        self,
        sdp: SessionDescription,
        *,
        tracker: str | CallbackData | None = None,
    ) -> SuccessResult:
        """
        Connect to a call by providing a call agent's SDP.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#accept-call>`_.

        You have about 30 to 60 seconds after the Call Connect Webhook is sent to accept the phone call. If your business does not respond, the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Args:
            sdp: Contains the session description protocol (SDP) type and description language.
            tracker: The data to track the call with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            Whether the call was accepted.
        """
        return await self._client.accept_call(call_id=self.id, sdp=sdp, tracker=tracker)

    async def reject(self) -> SuccessResult:
        """
        Reject the call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#reject-call>`_.

        You have about 30 to 60 seconds after the Call Connect webhook is sent to accept the phone call. If the business does not respond the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Returns:
            Whether the call was rejected.
        """
        return await self._client.reject_call(call_id=self.id)

    async def terminate(self) -> SuccessResult:
        """
        Terminate the active call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#terminate-call>`_.

        This must be done even if there is an RTCP BYE packet in the media path. Ending the call this way also ensures pricing is more accurate.
        When the WhatsApp user terminates the call, you do not have to call this endpoint. Once the call is successfully terminated, a Call Terminate Webhook will be sent to you.

        Returns:
            Whether the call was terminated.
        """
        return await self._client.terminate_call(call_id=self.id)


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallConnect(BaseUserUpdateAsync, _CallShortcutsAsync, _CallConnect):
    """
    Represents a call connection event.

    - This update arrives when a call is initiated by the business or the user.

    Attributes:
        id: The call ID.
        metadata: The metadata of the call (to which phone number this call was made or received).
        from_user: The user who participated in the call, either as caller or callee.
        timestamp: The timestamp when this call was made (in UTC).
        event: The calling event (always ``CONNECT``).
        direction: Whether the call was initiated by the business or the user.
        session: The session information, including SDP type and SDP info.
        shared_data: Shared data between handlers.
    """


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallTerminate(BaseUserUpdateAsync, _CallShortcutsAsync, _CallTerminate):
    """
    Represents a call termination event.

    - This update arrives when a call is terminated, either by the business or the user.

    Attributes:
        id: The call ID.
        metadata: The metadata of the call (to which phone number this call was made or received).
        from_user: The user who participated in the call, either as caller or callee.
        timestamp: The timestamp when this update is sent (in UTC).
        event: The calling event (always ``TERMINATE``).
        direction: Whether the call was initiated by the business or the user.
        status: The status of the call (either ``FAILED`` or ``COMPLETED``).
        start_time: The start time of the call in UTC (Only if the call was picked up).
        end_time: The end time of the call in UTC (Only if the call was picked up).
        duration: The duration of the call in seconds (Only if the call was picked up).
        tracker: The tracker that the call is initiated with.
        shared_data: Shared data between handlers.
    """

    async def recall(
        self, sdp: SessionDescription, *, tracker: str | CallbackData | None = None
    ) -> InitiatedCall:
        """
        Recall the call with the given SDP.

        - This is useful if you want to re-initiate a call after it has been terminated.

        Args:
            sdp: Contains the session description protocol (SDP) type and description language.
            tracker: The data to track the call with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            An InitiatedCall object containing the details of the initiated call.
        """
        return await self._client.initiate_call(
            to=self._internal_sender,
            sdp=sdp,
            tracker=tracker,
            phone_id=self._internal_recipient,
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallStatus(BaseUserUpdateAsync, _CallShortcutsAsync, _CallStatus):
    """
    Represents a call status update.

    - This update arrives when during a business-initiated call, the user either accepts or rejects the call.

    Attributes:
        id: The call ID.
        metadata: The metadata of the call (to which phone number this call was made or received).
        timestamp: The timestamp when this status update is sent (in UTC).
        type: The type of the status update (always "call").
        status: The status of the call (either "RINGING", "ACCEPTED", or "REJECTED").
        tracker: The tracker that the call is initiated with.
        shared_data: Shared data between handlers.
    """


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallPermissionUpdate(BaseUserUpdateAsync, _CallPermissionUpdate):
    """
    Represents a call permission update.

    - This update arrives when a call permission request is sent to the user, and the user responds with an action.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number this call permission request was sent).
        type: The type of the message (always ``INTERACTIVE``).
        reply_to_message: The message that this call permission request is replying to.
        from_user: The user who acted on the call permission request.
        timestamp: The timestamp when this update is sent (in UTC).
        response: The response to the call permission request (either ``ACCEPT`` or ``REJECT``).
        response_source: The source of the call permission response (either ``USER_ACTION`` or ``AUTOMATIC``).
        expiration_timestamp: The timestamp when the call permission request expires (if applicable).
    """
