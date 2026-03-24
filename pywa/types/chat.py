from __future__ import annotations

import dataclasses
import enum


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Chat:
    """
    Represents a chat.

    Attributes:
        id: The ID of the chat.
        type: The type of the chat (private or group).
    """

    id: str
    type: ChatType


class ChatType(enum.Enum):
    PRIVATE = enum.auto()
    GROUP = enum.auto()
