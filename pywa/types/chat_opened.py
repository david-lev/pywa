from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING

from .base_update import BaseUserUpdate  # noqa
from .others import (
    MessageType,
    Metadata,
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
        timestamp: The timestamp when this message was sent (in UTC).
        shared_data: Shared data between handlers.
    """

    type: MessageType

    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> ChatOpened:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "messages"
        ][0]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
        )
