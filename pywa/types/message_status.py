from __future__ import annotations

from .callback import CallbackDataT

"""This module contains the types related to message status updates."""

__all__ = [
    "MessageStatus",
    "MessageStatusType",
    "Conversation",
    "ConversationCategory",
]

import dataclasses
import logging
import datetime
from typing import TYPE_CHECKING, Generic

from .. import utils
from ..errors import WhatsAppError

from .base_update import BaseUserUpdate  # noqa
from .others import Metadata, User

if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)


class MessageStatusType(utils.StrEnum):
    """
    Message status type.

    Attributes:
        SENT: The message was sent.
        DELIVERED: The message was delivered.
        READ: The message was read.
        FAILED: The message failed to send (you can access the ``.error`` attribute for more information).
    """

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

    @classmethod
    def _missing_(cls, value: str) -> MessageStatusType:
        _logger.warning("Unknown message status type: %s. Defaulting to FAILED.", value)
        return cls.FAILED


class ConversationCategory(utils.StrEnum):
    """
    Conversation category.

    Attributes:
        AUTHENTICATION: The conversation is related to authentication.
        MARKETING: The conversation is related to marketing.
        UTILITY: The conversation is related to utility.
        SERVICE: The conversation is related to service.
        REFERRAL_CONVERSION: The conversation is related to referral conversion.
        UNKNOWN: The conversation category is unknown.
    """

    AUTHENTICATION = "authentication"
    MARKETING = "marketing"
    UTILITY = "utility"
    SERVICE = "service"
    REFERRAL_CONVERSION = "referral_conversion"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: str) -> ConversationCategory:
        _logger.warning(
            "Unknown conversation category: %s. Defaulting to UNKNOWN.", value
        )
        return cls.UNKNOWN


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class MessageStatus(BaseUserUpdate, Generic[CallbackDataT]):
    """
    Represents the status of a message.

    - `'MessageStatus' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object>`_.

    ``MessageStatus`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``tracker`` attribute.

    Here is an example:

        >>> from pywa.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa import WhatsApp
        >>> from pywa.types import Button, CallbackButton
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Hi user',
        ...     tracker=UserData(id=123, name='david', admin=True) # Here ^^^ we use the UserData class as the tracker
        ... )           # Here ^^^ we use the UserData class as the tracker data

        >>> @wa.on_message_status(factory=UserData) # Use the factory parameter to convert the tracker data
        ... def on_status(_: WhatsApp, s: MessageStatus[UserData]): # For autocomplete
        ...    if s.tracker.admin: print(s.tracker.id) # Access the tracker data

    You can even use multiple factories, and not only ``CallbackData`` subclasses!

        >>> from enum import Enum
        >>> class State(str, Enum):
        ...     START = 's'
        ...     END = 'e'

        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Hi user',
        ...     tracker=(UserData(id=123, name='david', admin=True), State.START)
        ... )           # Here ^^^ we send a tuple of UserData and State

        >>> @wa.on_message_status(factory=(UserData, State)) # Use the factory parameter to convert the tracker data
        ... def on_user_data(_: WhatsApp, s: MessageStatus[tuple[UserData, State]]): # For autocomplete
        ...    user, state = s.tracker # Unpack the tuple
        ...    if user.admin: print(user.id, state)


    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        from_user: The user who the message was sent to.
        tracker: The tracker that the message was sent with (e.g. ``wa.send_message(tracker=...)``).
        conversation: The conversation the given status notification belongs to (Optional).
        pricing_model: Type of pricing model used by the business. Current supported value is CBP.
        error: The error that occurred (if status is :class:`MessageStatusType.FAILED`).
    """

    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    status: MessageStatusType
    tracker: CallbackDataT | None
    conversation: Conversation | None
    pricing_model: str | None
    error: WhatsAppError | None

    _txt_fields = ("tracker",)

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> MessageStatus:
        status = (value := update["entry"][0]["changes"][0]["value"])["statuses"][0]
        error = value.get("errors", status.get("errors", (None,)))[0]
        return cls(
            _client=client,
            raw=update,
            id=status["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            status=MessageStatusType(status["status"]),
            timestamp=datetime.datetime.fromtimestamp(int(status["timestamp"])),
            from_user=User(wa_id=status["recipient_id"], name=None),
            tracker=status.get("biz_opaque_callback_data"),
            conversation=Conversation.from_dict(status["conversation"])
            if "conversation" in status
            else None,
            pricing_model=status.get("pricing", {}).get("pricing_model"),
            error=WhatsAppError.from_dict(error=error) if error else None,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Conversation:
    """
    Represents a conversation.

    - `'Conversation' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/pricing#conversations>`_.

    Attributes:
        id: The ID of the conversation.
        category: The category of the conversation.
        expiration: The expiration date of the conversation (Optional, only for `sent` updates).

    """

    id: str
    category: ConversationCategory
    expiration: datetime.datetime | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            category=ConversationCategory(data["origin"]["type"]),
            expiration=datetime.datetime.fromtimestamp(
                int(data["expiration_timestamp"])
            )
            if "expiration_timestamp" in data
            else None,
        )
