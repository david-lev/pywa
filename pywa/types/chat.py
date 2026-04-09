from __future__ import annotations

import dataclasses
import enum

from .user import User


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

    @classmethod
    def from_message(cls, msg: dict, user: User) -> Chat:
        return (
            cls(id=msg["group_id"], type=ChatType.GROUP)
            if "group_id" in msg
            else Chat(id=user.preferred_id, type=ChatType.PRIVATE)
        )


class ChatType(enum.Enum):
    PRIVATE = enum.auto()
    GROUP = enum.auto()
