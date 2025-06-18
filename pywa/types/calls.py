from __future__ import annotations

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
