from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from .base_update import BaseUpdate
from .others import MessageType, Metadata, User, ReplyToMessage

if TYPE_CHECKING:
    from pywa.client import WhatsApp


@dataclass(frozen=True, slots=True)
class CallbackButton(BaseUpdate):
    """
    Represents a callback button.

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always ``interactive``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback button is a reply to.
        data: The data of the button.
        title: The title of the button.
    """
    reply_to_message: ReplyToMessage
    data: str
    title: str

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to"""
        return self.reply_to_message.message_id

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata.from_dict(**value['metadata']),
            type=MessageType(message['type']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            reply_to_message=ReplyToMessage.from_dict(message['context']),
            data=message['interactive']['button_reply']['id'],
            title=message['interactive']['button_reply']['title']
        )


@dataclass(frozen=True, slots=True)
class CallbackSelection(BaseUpdate):
    """
    Represents a callback selection.

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always ``interactive``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback selection is a reply to.
        data: The data of the selection.
        title: The title of the selection.
        description: The description of the selection (optional).
    """
    reply_to_message: ReplyToMessage
    data: str
    title: str
    description: str | None

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to"""
        return self.reply_to_message.message_id

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata.from_dict(**value['metadata']),
            type=MessageType(message['type']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            reply_to_message=ReplyToMessage.from_dict(message['context']),
            data=message['interactive']['list_reply']['id'],
            title=message['interactive']['list_reply']['title'],
            description=message['interactive']['list_reply'].get('description')
        )


@dataclass(frozen=True, slots=True)
class InlineButton:
    """
    Represents an inline button in a keyboard.

    Attributes:
        title: The title of the button (up to 20 characters).
        callback_data: The payload to send when the user clicks on the button (up to 256 characters).
    """
    title: str
    callback_data: str

    def to_dict(self) -> dict:
        return {"type": "reply", "reply": {"id": self.callback_data, "title": self.title}}


@dataclass(frozen=True, slots=True)
class SectionRow:
    """
    Represents a row in a section.

    Attributes:
        title: The title of the row (up to 24 characters).
        callback_data: The payload to send when the user clicks on the row (up to 200 characters).
        description: The description of the row (optional, up to 72 characters).
    """
    title: str
    callback_data: str
    description: str | None = None

    def to_dict(self) -> dict:
        d = {"id": self.callback_data, "title": self.title}
        if self.description:
            d["description"] = self.description
        return d


@dataclass(frozen=True, slots=True)
class Section:
    """
    Represents a section in a section list.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object

    Attributes:
        title: The title of the section.
        rows: The rows in the section (at least 1, no more than 10).
    """
    title: str
    rows: list[SectionRow]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "rows": [row.to_dict() for row in self.rows]
        }


@dataclass(frozen=True, slots=True)
class SectionList:
    """
    Represents a section list in an interactive message.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object

    Attributes:
        button_title: The title of the button that opens the section list (up to 20 characters).
        sections: The sections in the section list (at least 1, no more than 10).
    """
    button_title: str
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "button": self.button_title,
            "sections": [section.to_dict() for section in self.sections]
        }
