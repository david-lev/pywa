from __future__ import annotations

import dataclasses
import enum


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Chat:
    id: str
    type: ChatType


class ChatType(enum.Enum):
    PRIVATE = enum.auto()
    GROUP = enum.auto()
