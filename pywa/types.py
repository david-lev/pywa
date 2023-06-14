from datetime import datetime
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from pywa import WhatsApp


@dataclass(frozen=True, slots=True)
class Button:
    id: str
    title: str

    def to_dict(self) -> dict:
        return {"type": "reply", "reply": {"id": self.id, "title": self.title}}


@dataclass(frozen=True, slots=True)
class SectionRow:
    id: str
    title: str
    description: str | None = None

    def to_dict(self) -> dict:
        d = {"id": self.id, "title": self.title}
        if self.description:
            d["description"] = self.description
        return d


@dataclass(frozen=True, slots=True)
class Section:
    """https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object"""
    title: str
    rows: list[SectionRow]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "rows": [row.to_dict() for row in self.rows]
        }


@dataclass(frozen=True, slots=True)
class SectionList:
    """https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object"""
    button: str
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "button": self.button,
            "sections": [section.to_dict() for section in self.sections]
        }


@dataclass(frozen=True, slots=True)
class User:
    wa_id: str
    name: str


class MessageType(str, Enum):
    AUDIO = "audio"
    DOCUMENT = "document"
    TEXT = "text"
    IMAGE = "image"
    INTERACTIVE = "interactive"
    STICKER = "sticker"
    VIDEO = "video"
    REACTION = "reaction"
    # CONTACTS = "contacts"
    # SYSTEM = "system"
    # ORDER = "order"
    UNSUPPORTED = "unsupported"

    @classmethod
    def _missing_(cls, value):
        return cls.UNSUPPORTED

    def __str__(self):
        return self.value


class MediaBase:
    __slots__ = ('id', 'sha256', 'mime_type')
    id: str
    sha256: str
    mime_type: str


@dataclass(frozen=True, slots=True)
class Image(MediaBase):
    pass


@dataclass(frozen=True, slots=True)
class Video(MediaBase):
    pass


@dataclass(frozen=True, slots=True)
class Sticker(MediaBase):
    animated: bool


@dataclass(frozen=True, slots=True)
class Document(MediaBase):
    filename: str


@dataclass(frozen=True, slots=True)
class Audio(MediaBase):
    voice: bool


@dataclass(frozen=True, slots=True)
class Reaction:
    message_id: str
    emoji: str

class BaseNotification:
    __slots__ = ('id', 'from_user', 'timestamp')
    id: str
    from_user: User
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class Message(BaseNotification):
    _client: WhatsApp
    type: MessageType
    reply_to_message_id: str | None
    text: str | None
    image: Image | None
    video: Video | None
    sticker: Sticker | None
    document: Document | None
    audio: Audio | None
    reaction: Reaction | None

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CallbackButtonReply(BaseNotification):
    callback_id: str
    callback_title: str

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CallbackListReply(BaseNotification):
    callback_id: str
    callback_title: str
    callback_description: str | None

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        raise NotImplementedError
