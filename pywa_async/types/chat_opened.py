from __future__ import annotations

__all__ = ["ChatOpened"]

from pywa.types.chat_opened import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.chat_opened import ChatOpened as _ChatOpened  # noqa MUST BE IMPORTED FIRST
from .base_update import BaseUserUpdateAsync  # noqa

import dataclasses


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class ChatOpened(BaseUserUpdateAsync, _ChatOpened):
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
