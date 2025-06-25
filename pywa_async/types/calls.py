from pywa.types.calls import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.calls import (
    CallConnect as _CallConnect,
    CallTerminate as _CallTerminate,
    CallStatus as _CallStatus,
)
from .base_update import BaseUserUpdateAsync  # noqa


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallConnect(BaseUserUpdateAsync, _CallConnect):
    """
    Represents a call connection event.

    - This update arrives when a call is initiated by the business.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number this call was made).
        from_user: The user who made the call.
        timestamp: The timestamp when this call was made (in UTC).
        event: The calling event (always "connect").
        direction: The direction of the call (either "BUSINESS_INITIATED" or "USER_INITIATED").
        session: The session information, including SDP type and SDP info.
        shared_data: Shared data between handlers.
    """

    async def pre_accept(self, sdp: SDP) -> bool:
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
        sdp: SDP,
        tracker: str | CallbackData | None = None,
    ) -> bool:
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

    async def reject(self) -> bool:
        """
        Reject the call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#reject-call>`_.

        You have about 30 to 60 seconds after the Call Connect webhook is sent to accept the phone call. If the business does not respond the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Returns:
            Whether the call was rejected.
        """
        return await self._client.reject_call(call_id=self.id)

    async def terminate(self) -> bool:
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
class CallTerminate(BaseUserUpdateAsync, _CallTerminate):
    """
    Represents a call termination event.

    - This update arrives when a call is terminated, either by the business or the user.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number this call was made).
        from_user: The user who made the call.
        timestamp: The timestamp when this call was made (in UTC).
        event: The calling event (always "terminate").
        direction: The direction of the call (either "BUSINESS_INITIATED" or "USER_INITIATED").
        status: The status of the call (either "FAILED" or "COMPLETED").
        start_time: The start time of the call in UTC (Only if the call was picked up).
        end_time: The end time of the call in UTC (Only if the call was picked up).
        duration: The duration of the call in seconds (Only if the call was picked up).
        tracker: The tracker that the call is initiated with.
        shared_data: Shared data between handlers.
    """


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallStatus(BaseUserUpdateAsync, _CallStatus):
    """
    Represents a call status update.

    This update arrives when during a business-initiated call, the user either accepts or rejects the call.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number this call was made).
        timestamp: The timestamp when this call was made (in UTC).
        type: The type of the status update (always "call").
        status: The status of the call (either "RINGING", "ACCEPTED", or "REJECTED").
        tracker: The tracker that the call is initiated with.
        shared_data: Shared data between handlers.
    """
