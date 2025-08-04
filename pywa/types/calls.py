from __future__ import annotations

from . import MessageType

"""This module contains types related to WhatsApp calls, including call connection, termination, and status updates."""

__all__ = [
    "CallPermissionUpdate",
    "CallPermissionResponse",
    "CallPermissionResponseSource",
    "CallConnect",
    "SessionDescription",
    "CallEvent",
    "CallDirection",
    "CallTerminate",
    "CallTerminateStatus",
    "CallStatus",
    "CallStatusType",
    "CallingSettingsStatus",
    "CallIconVisibility",
    "CallbackPermissionStatus",
    "SIPStatus",
    "SIPServer",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "HolidaySchedule",
    "CallHours",
    "CallingSettings",
    "BusinessPhoneNumberSettings",
    "CallPermissionStatus",
    "CallPermissionActionLimit",
    "CallPermissionAction",
    "CallPermission",
    "CallPermissionActionLimit",
    "CallPermissionAction",
    "CallPermissions",
]

import dataclasses
import datetime
from typing import TYPE_CHECKING, Generic

from .base_update import BaseUserUpdate, BaseUpdate, _ClientShortcuts  # noqa
from .others import (
    Metadata,
    SuccessResult,
    ReplyToMessage,
    StorageConfiguration,
)
from .callback import _CallbackDataT, CallbackData
from .. import utils
from ..errors import WhatsAppError

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .sent_update import InitiatedCall


class _CallShortcuts:
    """Base class for call actions."""

    id: str
    _client: WhatsApp
    _internal_sender: str
    _internal_recipient: str

    @property
    def message_id_to_reply(self) -> str:
        """Raises an error because call terminate updates cannot be replied."""
        raise ValueError("You cannot use `message_id_to_reply` to quote a call update.")

    @property
    def caller(self) -> str:
        """
        The WhatsApp ID of the business phone number that initiated the call.
        """
        return self._internal_recipient

    @property
    def callee(self) -> str:
        """The WhatsApp ID of the user that received the call."""
        return self._internal_sender

    def pre_accept(self, *, sdp: SessionDescription) -> SuccessResult:
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
        return self._client.pre_accept_call(call_id=self.id, sdp=sdp)

    def accept(
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
        return self._client.accept_call(call_id=self.id, sdp=sdp, tracker=tracker)

    def reject(self) -> SuccessResult:
        """
        Reject the call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#reject-call>`_.

        You have about 30 to 60 seconds after the Call Connect webhook is sent to accept the phone call. If the business does not respond the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Returns:
            Whether the call was rejected.
        """
        return self._client.reject_call(call_id=self.id)

    def terminate(self) -> SuccessResult:
        """
        Terminate the active call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#terminate-call>`_.

        This must be done even if there is an RTCP BYE packet in the media path. Ending the call this way also ensures pricing is more accurate.
        When the WhatsApp user terminates the call, you do not have to call this endpoint. Once the call is successfully terminated, a Call Terminate Webhook will be sent to you.

        Returns:
            Whether the call was terminated.
        """
        return self._client.terminate_call(call_id=self.id)


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallConnect(BaseUserUpdate, _CallShortcuts):
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

    event: CallEvent
    direction: CallDirection
    session: SessionDescription | None

    _webhook_field = "calls"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> CallConnect:
        call = (value := (entry := update["entry"][0])["changes"][0]["value"])["calls"][
            0
        ]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=call["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client)
            if "contacts" in value  # Only available for USER_INITIATED calls
            else client._usr_cls(_client=client, wa_id=call["to"], name=None),
            timestamp=datetime.datetime.fromtimestamp(
                int(call["timestamp"]),
                datetime.timezone.utc,
            ),
            event=CallEvent(call["event"]),
            direction=CallDirection(call["direction"]),
            session=SessionDescription.from_dict(call["session"])
            if "session" in call
            else None,
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallPermissionUpdate(BaseUserUpdate):
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

    type: MessageType
    reply_to_message: ReplyToMessage
    response: CallPermissionResponse
    response_source: CallPermissionResponseSource
    expiration_timestamp: datetime.datetime | None = None

    _webhook_field = "messages"

    def __bool__(self):
        """
        Returns True if the call permission request was accepted.
        """
        return self.response != CallPermissionResponse.REJECT

    @property
    def is_expired(self) -> bool:
        """
        Whether the call permission request has expired.
        """
        return (
            self.expiration_timestamp is not None
            and self.expiration_timestamp < datetime.datetime.now(datetime.timezone.utc)
        )

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> CallPermissionUpdate:
        perm = (
            msg := (value := (entry := update["entry"][0])["changes"][0]["value"])[
                "messages"
            ][0]
        )["interactive"]["call_permission_reply"]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls(
                _client=client,
                wa_id=msg["from"],
                name=None,
            ),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            reply_to_message=ReplyToMessage.from_dict(msg["context"])
            if msg.get("context", {}).get("id")
            else None,
            response=CallPermissionResponse(perm["response"]),
            response_source=CallPermissionResponseSource(perm["response_source"]),
            expiration_timestamp=datetime.datetime.fromtimestamp(
                int(perm.get("expiration_timestamp", 0)),
                datetime.timezone.utc,
            )
            if "expiration_timestamp" in perm
            else None,
        )


class CallPermissionResponse(utils.StrEnum):
    """
    Represents the response to a call permission request.

    Attributes:
        ACCEPT: The user accepted the call permission request.
        REJECT: The user rejected the call permission request.
    """

    _check_value = str.islower
    _modify_value = str.lower

    ACCEPT = "accept"
    REJECT = "reject"

    UNKNOWN = "UNKNOWN"


class CallPermissionResponseSource(utils.StrEnum):
    """
    Represents the source of the call permission response.

    Attributes:
        USER_ACTION: User approved or rejected the permission
        AUTOMATIC: An automatic permission approval due to the WhatsApp user initiating the call
    """

    _check_value = str.islower
    _modify_value = str.lower

    USER_ACTION = "user_action"
    AUTOMATIC = "automatic"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class SessionDescription(utils.FromDict):
    """
    Contains the Session Description Protocol (SDP) type and description language.

    - `Learn more about Session Description Protocol (SDP) <https://www.rfc-editor.org/rfc/rfc8866.html?fbclid=IwZXh0bgNhZW0CMTAAYnJpZBExZ29GWHBsSlEyRXA1aThYMgEeF-jEVWkTrJf0tEEbpY0iS9kkCIFncddV7i-RU-qm_eAD0MG6oE3oIwsNUWY_aem_X06J-leL4yOl1-TWuaMyoQ>`_.
    - `View example SDP structures <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/reference#sdp-overview-and-sample-sdp-structures>`_.

    Attributes:
        sdp_type: "offer", to indicate SDP offer
        sdp: The SDP info of the device on the other end of the call. The SDP must be compliant with `RFC 8866 <https://datatracker.ietf.org/doc/html/rfc8866?fbclid=IwZXh0bgNhZW0CMTAAYnJpZBExaENMd1p1NEpTbkQyQlNpMgEeyPkNeWi6AvgR4q8vdCIMx6rJ4AWd4yxRYpn6mvZ31VjC_0fN6FtPdrxtDOs_aem_7po_7yOAFkrlcV4Xn3TVnQ>`_.
    """

    sdp_type: str
    sdp: str

    def to_dict(self) -> dict[str, str]:
        return {
            "sdp_type": self.sdp_type,
            "sdp": self.sdp,
        }


class CallEvent(utils.StrEnum):
    """
    Represents the type of call event.

    Attributes:
        CONNECT: The call is connected.
        TERMINATE: The call is terminated.
    """

    _check_value = str.islower
    _modify_value = str.lower

    CONNECT = "connect"
    TERMINATE = "terminate"

    UNKNOWN = "UNKNOWN"


class CallDirection(utils.StrEnum):
    """
    Represents the direction of a call (who initiated the call).

    Attributes:
        BUSINESS_INITIATED: The call was initiated by the business.
        USER_INITIATED: The call was initiated by the user.
    """

    BUSINESS_INITIATED = "BUSINESS_INITIATED"
    USER_INITIATED = "USER_INITIATED"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallTerminate(BaseUserUpdate, _CallShortcuts, Generic[_CallbackDataT]):
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

    event: CallEvent
    direction: CallDirection
    status: CallTerminateStatus
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None
    duration: int | None
    error: WhatsAppError | None
    tracker: _CallbackDataT | None

    _webhook_field = "calls"

    @property
    def message_id_to_reply(self) -> str:
        """Raises an error because call terminate updates cannot be replied."""
        raise ValueError(
            "You cannot use `message_id_to_reply` to quote a call terminate update."
        )

    @classmethod
    def from_update(
        cls, client: WhatsApp, update: dict
    ) -> CallTerminate[_CallbackDataT]:
        call = (value := (entry := update["entry"][0])["changes"][0]["value"])["calls"][
            0
        ]
        error = value.get("errors", (None,))[0]
        direction = CallDirection(call["direction"])
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=call["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls(
                _client=client,
                wa_id=call["from"]
                if direction == CallDirection.BUSINESS_INITIATED
                else call["to"],
                name=None,
            ),
            timestamp=datetime.datetime.fromtimestamp(
                int(call["timestamp"]),
                datetime.timezone.utc,
            ),
            event=CallEvent(call["event"]),
            direction=direction,
            status=CallTerminateStatus(call["status"]),
            start_time=datetime.datetime.fromtimestamp(
                int(call["start_time"]), datetime.timezone.utc
            )
            if "start_time" in call
            else None,
            end_time=datetime.datetime.fromtimestamp(
                int(call["end_time"]), datetime.timezone.utc
            )
            if "end_time" in call
            else None,
            duration=int(call["duration"]) if "duration" in call else None,
            error=WhatsAppError.from_dict(error) if error else None,
            tracker=call.get("biz_opaque_callback_data"),
        )

    def recall(
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
        return self._client.initiate_call(
            to=self._internal_sender,
            sdp=sdp,
            tracker=tracker,
            phone_id=self._internal_recipient,
        )


class CallTerminateStatus(utils.StrEnum):
    """
    Represents the status of a call termination event.

    Attributes:
        FAILED: The call failed.
        COMPLETED: The call was completed successfully.
    """

    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallStatus(BaseUserUpdate, _CallShortcuts, Generic[_CallbackDataT]):
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

    type: str
    status: CallStatusType
    tracker: _CallbackDataT | None = None

    _webhook_field = "calls"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> CallStatus:
        status = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "statuses"
        ][0]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=status["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            timestamp=datetime.datetime.fromtimestamp(
                int(status["timestamp"]),
                datetime.timezone.utc,
            ),
            from_user=client._usr_cls(
                wa_id=status["recipient_id"], name=None, _client=client
            ),
            type=status["type"],
            status=CallStatusType(status["status"]),
            tracker=status.get("biz_opaque_callback_data"),
        )


class CallStatusType(utils.StrEnum):
    """
    Represents the type of call status.

    Attributes:
        RINGING: Business initiated call is ringing the user.
        ACCEPTED: Business initiated call is accepted by the user.
        REJECTED: Business initiated call is rejected by the user.
    """

    RINGING = "RINGING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    UNKNOWN = "UNKNOWN"


class CallingSettingsStatus(utils.StrEnum):
    """
    Represents the status of calling settings.
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

    UNKNOWN = "UNKNOWN"


class CallIconVisibility(utils.StrEnum):
    """
    Represents the visibility of the call icon.
    """

    DEFAULT = "DEFAULT"
    DISABLE_ALL = "DISABLE_ALL"

    UNKNOWN = "UNKNOWN"


class CallbackPermissionStatus(utils.StrEnum):
    """
    Represents the status of callback permission.
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

    UNKNOWN = "UNKNOWN"


class SIPStatus(utils.StrEnum):
    """
    Represents the status of SIP (Session Initiation Protocol).
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class SIPServer(utils.FromDict):
    """
    Represents a SIP server configuration.

    Attributes:
        hostname: The hostname of the SIP server.
        port: The port of the SIP server.
        request_uri_user_params: Optional parameters for the request URI user.
        sip_user_password: The password for the SIP user (only if ``include_sip_credentials`` is True).
    """

    hostname: str
    port: int
    request_uri_user_params: dict[str, str] | None
    sip_user_password: str | None


@dataclasses.dataclass(slots=True, kw_only=True)
class WeekDay:
    """
    Represents a day of the week with its opening and closing times.

    - You can use the subclasses for specific days (e.g., :class:`Monday`, ``Tuesday``, etc.) to create instances with predefined day names.

    Attributes:
        day_of_week: The day of the week (e.g., "MONDAY", "TUESDAY").
        open_time: The opening time in 24-hour format (e.g., "0400" for 4:00 AM).
        close_time: The closing time in 24-hour format (e.g., "2200" for 10:00 PM).
    """

    day_of_week: str
    open_time: datetime.time
    close_time: datetime.time

    def to_dict(self) -> dict[str, str]:
        return {
            "day_of_week": self.day_of_week,
            "open_time": self.open_time.strftime("%H%M"),
            "close_time": self.close_time.strftime("%H%M"),
        }


@dataclasses.dataclass(slots=True, kw_only=True)
class Monday(WeekDay):
    """
    Represents Monday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="MONDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Tuesday(WeekDay):
    """
    Represents Tuesday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="TUESDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Wednesday(WeekDay):
    """
    Represents Wednesday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="WEDNESDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Thursday(WeekDay):
    """
    Represents Thursday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="THURSDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Friday(WeekDay):
    """
    Represents Friday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="FRIDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Saturday(WeekDay):
    """
    Represents Saturday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="SATURDAY", init=False, repr=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Sunday(WeekDay):
    """
    Represents Sunday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="SUNDAY", init=False, repr=False)


_day_to_weekday_map = {
    "MONDAY": Monday,
    "TUESDAY": Tuesday,
    "WEDNESDAY": Wednesday,
    "THURSDAY": Thursday,
    "FRIDAY": Friday,
    "SATURDAY": Saturday,
    "SUNDAY": Sunday,
}


def _day_to_weekday(day: dict[str, str]) -> WeekDay:
    """
    Converts a dictionary representation of a day to a WeekDay object.

    Args:
        day: A dictionary containing the day of the week, open time, and close time.

    Returns:
        An instance of a specific WeekDay subclass based on the day of the week.
    """
    # noinspection PyArgumentList
    return _day_to_weekday_map[day["day_of_week"]](
        open_time=datetime.datetime.strptime(day["open_time"], "%H%M").time(),
        close_time=datetime.datetime.strptime(day["close_time"], "%H%M").time(),
    )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class HolidaySchedule:
    """
    Represents a holiday schedule with a date and opening/closing times.

    Attributes:
        date: The date of the holiday.
        start_time: The opening time in 24-hour format (e.g., "0000" for midnight).
        end_time: The closing time in 24-hour format (e.g., "2359" for 11:59 PM).
    """

    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time

    def to_dict(self) -> dict[str, str]:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "start_time": self.start_time.strftime("%H%M"),
            "end_time": self.end_time.strftime("%H%M"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> HolidaySchedule:
        return cls(
            date=datetime.datetime.strptime(data["date"], "%Y-%m-%d").date(),
            start_time=datetime.datetime.strptime(data["start_time"], "%H%M").time(),
            end_time=datetime.datetime.strptime(data["end_time"], "%H%M").time(),
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallHours:
    """
    Represents the call hours settings for a business.

    - Maximum of 2 entries allowed per day of week
    - open_time must be before close_time
    - Overlapping entries not allowed

    Attributes:
        status: Enable or disable the call hours for the business (If call hours are disabled, the business is considered open all 24 hours of the day, 7 days a week).
        timezone_id: The timezone that the business is operating within. `Learn more about supported values for timezone_id <https://developers.facebook.com/docs/facebook-business-extension/fbe/reference#time-zones>`_.
        weekly_operating_hours: The operating hours schedule for each day of the week.
        holiday_schedule: An optional override to the weekly schedule, Up to 20 overrides can be specified. Note: If holiday_schedule is not passed in the request, then the existing holiday_schedule will be deleted and replaced with an empty schedule.
    """

    status: CallingSettingsStatus
    timezone_id: str
    weekly_operating_hours: list[WeekDay]
    holiday_schedule: list[HolidaySchedule] | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "timezone_id": self.timezone_id,
            "weekly_operating_hours": [
                day.to_dict() for day in self.weekly_operating_hours
            ],
            "holiday_schedule": [holiday.to_dict() for holiday in self.holiday_schedule]
            if self.holiday_schedule
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CallHours:
        return cls(
            status=CallingSettingsStatus(data["status"]),
            timezone_id=data["timezone_id"],
            weekly_operating_hours=[
                _day_to_weekday(day) for day in data["weekly_operating_hours"]
            ],
            holiday_schedule=[
                HolidaySchedule.from_dict(holiday)
                for holiday in data.get("holiday_schedule", [])
            ]
            if "holiday_schedule" in data
            else None,
        )


class STRPKeyExchangeProtocol(utils.StrEnum):
    """
    Represents the SRTP key exchange protocol.

    Attributes:
        DTLS: Datagram Transport Layer Security (DTLS) is used for key exchange.
        SDES: Session Description Protocol Security Descriptions (SDES) is used for key exchange.
    """

    DTLS = "DTLS"
    SDES = "SDES"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class CallingSettings:
    """
    Represents the calling settings for a business phone number.

    - See `Configure Call Settings <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/call-settings>`_ for more details.

    Attributes:
        status: Enable or disable the Calling API for the given business phone number.
        call_icon_visibility: Configure whether the WhatsApp call button icon displays for users when chatting with the business. See `Call Icon Visibility <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/call-settings#parameter-details>`_ for more details.
        call_hours: Allows you specify and trigger call settings for incoming calls based on your timezone, business operating hours, and holiday schedules.
        callback_permission_status: Configure whether a WhatsApp user is prompted with a call permission request after calling your business.
        sip: Configure call signaling via signal initiation protocol (SIP). Note: When SIP is enabled, you cannot use calling related endpoints and will not receive calling related webhooks.
    """

    status: CallingSettingsStatus | None = None
    call_icon_visibility: CallIconVisibility | None = None
    call_hours: CallHours | None = None
    callback_permission_status: CallbackPermissionStatus | None = None
    srtp_key_exchange_protocol: STRPKeyExchangeProtocol | None = None
    sip: SIPServer | None = None

    def to_dict(self):
        data = {}
        if self.status:
            data["status"] = self.status.value
        if self.call_icon_visibility:
            data["call_icon_visibility"] = self.call_icon_visibility.value
        if self.callback_permission_status:
            data["callback_permission_status"] = self.callback_permission_status.value
        if self.call_hours:
            data["call_hours"] = self.call_hours.to_dict()
        if self.srtp_key_exchange_protocol:
            data["srtp_key_exchange_protocol"] = self.srtp_key_exchange_protocol.value
        if self.sip:
            data["sip"] = dataclasses.asdict(self.sip)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> CallingSettings:
        return cls(
            status=CallingSettingsStatus(data["status"]) if "status" in data else None,
            call_icon_visibility=CallIconVisibility(data["call_icon_visibility"])
            if "call_icon_visibility" in data
            else None,
            call_hours=CallHours.from_dict(data["call_hours"])
            if "call_hours" in data
            else None,
            callback_permission_status=CallbackPermissionStatus(
                data["callback_permission_status"]
            )
            if "callback_permission_status" in data
            else None,
            srtp_key_exchange_protocol=STRPKeyExchangeProtocol(
                data["srtp_key_exchange_protocol"]
            )
            if "srtp_key_exchange_protocol" in data
            else None,
            sip=SIPServer.from_dict(data["sip"]) if "sip" in data else None,
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class BusinessPhoneNumberSettings(utils.APIObject):
    """
    Represents the settings of a WhatsApp Business Phone Number.

    Attributes:
        calling: The calling settings of the phone number.
        storage_configuration: The storage configuration for the phone number.
    """

    calling: CallingSettings | None = None
    storage_configuration: StorageConfiguration

    @classmethod
    def from_dict(cls, data: dict) -> BusinessPhoneNumberSettings:
        return cls(
            calling=CallingSettings.from_dict(data.get("calling"))
            if data.get("calling")
            else None,
            storage_configuration=StorageConfiguration.from_dict(
                data["storage_configuration"]
            ),
        )

    def to_dict(self) -> dict:
        return {"calling": self.calling.to_dict() if self.calling else None}


class CallPermissionStatus(utils.StrEnum):
    """
    Represents the status of a call permission.

    Attributes:
        NO_PERMISSION: No permission granted.
        TEMPORARY: Temporary permission granted.
    """

    _check_value = str.islower
    _modify_value = str.lower

    NO_PERMISSION = "no_permission"
    TEMPORARY = "temporary"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallPermissionActionLimit:
    """
    Represents a limit for a specific action that can be performed with the call permission.

    Attributes:
        time_period: The time period for which the limit applies, represented in ISO 8601 format (e.g., "PT24H" for 24 hours).
        max_allowed: The maximum number of actions allowed within the specified time period.
        current_usage: The current number of actions taken within the specified time period.
        limit_expiration_time: The Unix time at which the limit will expire in UTC timezone (optional).
    """

    time_period: str
    max_allowed: int
    current_usage: int
    limit_expiration_time: datetime.datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CallPermissionActionLimit:
        return cls(
            time_period=data["time_period"],
            max_allowed=data["max_allowed"],
            current_usage=data["current_usage"],
            limit_expiration_time=datetime.datetime.fromtimestamp(
                data["limit_expiration_time"], datetime.timezone.utc
            )
            if "limit_expiration_time" in data
            else None,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallPermissionAction:
    """
    Represents an action that can be performed with the call permission.

    Attributes:
        action_name: The name of the action (e.g., "send_call_permission_request").
        can_perform_action: Whether the action can be performed.
        limits: A list of limits associated with the action.
    """

    action_name: str
    can_perform_action: bool
    limits: list[CallPermissionActionLimit]

    @classmethod
    def from_dict(cls, data: dict) -> CallPermissionAction:
        return cls(
            action_name=data["action_name"],
            can_perform_action=data["can_perform_action"],
            limits=[
                CallPermissionActionLimit.from_dict(limit) for limit in data["limits"]
            ],
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallPermission:
    """
    Represents a call permission with its status and expiration time.

    Attributes:
        status: The current status of the permission.
        expiration_time: The time at which the permission will expire in UTC timezone.
    """

    status: CallPermissionStatus
    expiration_time: datetime.datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CallPermission:
        return cls(
            status=CallPermissionStatus(data["status"]),
            expiration_time=datetime.datetime.fromtimestamp(
                data["expiration_time"], datetime.timezone.utc
            )
            if "expiration_time" in data
            else None,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallPermissions:
    """
    Represents the call permissions to specific WhatsApp user.

    - Read more about `Call Permissions <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-call-permissions>`_.

    Attributes:
        permission: The call permission status and expiration time.
        actions: A list of actions that can be performed with the call permission.
    """

    permission: CallPermission
    actions: list[CallPermissionAction]

    @classmethod
    def from_dict(cls, data: dict) -> CallPermissions:
        return cls(
            permission=CallPermission.from_dict(data["permission"]),
            actions=[
                CallPermissionAction.from_dict(action) for action in data["actions"]
            ],
        )
