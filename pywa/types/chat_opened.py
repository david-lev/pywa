from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING

from .base_update import BaseUserUpdate  # noqa
from .others import (
    MessageType,
    Metadata,
    User,
)

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class ChatOpened(BaseUserUpdate):
    """
    Represents a chat opened in the first time by a user.

    - If the user deletes the chat and opens it again, this event will be triggered again.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers/conversational-components#welcome-messages>`__.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (Always ``MessageType.REQUEST_WELCOME``).
        from_user: The user who opened the chat.
        timestamp: The timestamp when this message was sent.
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> ChatOpened:
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
        )
