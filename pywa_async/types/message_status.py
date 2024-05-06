"""This module contains the types related to message status updates."""

from __future__ import annotations

from pywa.types.message_status import *  # noqa MUST BE IMPORTED FIRST

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

from ..errors import WhatsAppError
from .callback import CallbackDataT
from .base_update import BaseUserUpdate  # noqa
from .others import Metadata, User

if TYPE_CHECKING:
    from pywa.client import WhatsApp

_logger = logging.getLogger(__name__)


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
