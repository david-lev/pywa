from __future__ import annotations

"""This module contains types related to WhatsApp calls, including call connection, termination, and status updates."""

__all__ = ["CallConnect", "CallTerminate", "CallStatus", "CallingSettings"]

import dataclasses
import datetime
from typing import TYPE_CHECKING, Generic

from .base_update import BaseUserUpdate, BaseUpdate  # noqa
from .others import (
    Metadata,
)
from .callback import _CallbackDataT
from .. import utils
from ..errors import WhatsAppError

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallConnect(BaseUserUpdate):
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

    """

    event: CallEvent
    direction: CallDirection
    session: SDP | None

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> CallConnect:
        call = (value := update["entry"][0]["changes"][0]["value"])["calls"][0]
        return cls(
            _client=client,
            raw=update,
            id=call["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(call["timestamp"]),
                datetime.timezone.utc,
            ),
            event=CallEvent(call["event"]),
            direction=CallDirection(["direction"]),
            session=SDP.from_dict(call["session"]) if "session" in call else None,
        )

    def connect(self) -> bool: ...

    def pre_accept(self) -> bool: ...

    def accept(self) -> bool: ...

    def reject(self) -> bool: ...

    def terminate(self) -> bool: ...


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class SDP(utils.FromDict):
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


class CallEvent(utils.StrEnum):
    """
    Represents the type of call event.

    Attributes:
        CONNECT: The call is connected.
        TERMINATE: The call is terminated.
    """

    CONNECT = "connect"
    TERMINATE = "terminate"


class CallDirection(utils.StrEnum):
    """
    Represents the direction of a call.

    Attributes:
        BUSINESS_INITIATED: The call was initiated by the business.
        USER_INITIATED: The call was initiated by the user.
    """

    BUSINESS_INITIATED = "BUSINESS_INITIATED"
    USER_INITIATED = "USER_INITIATED"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallTerminate(BaseUserUpdate, Generic[_CallbackDataT]):
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

    event: CallEvent
    direction: CallDirection
    status: CallTerminateStatus
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None
    duration: int | None
    error: WhatsAppError | None
    tracker: _CallbackDataT | None

    @classmethod
    def from_update(
        cls, client: WhatsApp, update: dict
    ) -> CallTerminate[_CallbackDataT]:
        call = (value := update["entry"][0]["changes"][0]["value"])["calls"][0]
        error = value.get("errors", (None,))[0]
        return cls(
            _client=client,
            raw=update,
            id=call["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(call["timestamp"]),
                datetime.timezone.utc,
            ),
            event=CallEvent(call["event"]),
            direction=CallDirection(call["direction"]),
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


class CallTerminateStatus(utils.StrEnum):
    """
    Represents the status of a call termination event.

    Attributes:
        FAILED: The call failed.
        COMPLETED: The call was completed successfully.
    """

    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallStatus(BaseUserUpdate, Generic[_CallbackDataT]):
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
    """

    type: str
    status: CallStatusType
    tracker: _CallbackDataT | None = None

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> CallStatus:
        value = update["entry"][0]["changes"][0]["value"]
        status = value["statuses"][0]
        return cls(
            _client=client,
            raw=update,
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


class CallingSettingsStatus(utils.StrEnum):
    """
    Represents the status of calling settings.
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class CallIconVisibility(utils.StrEnum):
    """
    Represents the visibility of the call icon.
    """

    DEFAULT = "DEFAULT"
    DISABLE_ALL = "DISABLE_ALL"


class CallbackPermissionStatus(utils.StrEnum):
    """
    Represents the status of callback permission.
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class SIPStatus(utils.StrEnum):
    """
    Represents the status of SIP (Session Initiation Protocol).
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


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

    day_of_week: str = dataclasses.field(default="MONDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Tuesday(WeekDay):
    """
    Represents Tuesday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="TUESDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Wednesday(WeekDay):
    """
    Represents Wednesday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="WEDNESDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Thursday(WeekDay):
    """
    Represents Thursday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="THURSDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Friday(WeekDay):
    """
    Represents Friday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="FRIDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Saturday(WeekDay):
    """
    Represents Saturday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="SATURDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True)
class Sunday(WeekDay):
    """
    Represents Sunday with its opening and closing times.
    """

    day_of_week: str = dataclasses.field(default="SUNDAY", init=False)


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class HolidaySchedule(utils.FromDict):
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


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallHours(utils.FromDict):
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


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class CallingSettings(utils.FromDict):
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
        if self.sip:
            data["sip"] = dataclasses.asdict(self.sip)
        return data
