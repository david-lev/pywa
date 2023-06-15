from __future__ import annotations

__all__ = (
    "Message",
    "MessageType",
    "MessageStatus",
    "MessageStatusType",
    "CallbackButtonReply",
    "CallbackListReply",
    "Button",
    "SectionRow",
    "Section",
    "SectionList",
    "MessageStatus",
)

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pywa.errors import WhatsAppError
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pywa.client import WhatsApp


@dataclass(frozen=True, slots=True)
class Button:
    """
    Represents a button in a keyboard.

    Attributes:
        id: The ID of the button (You get this ID when the user clicks on the button).
        title: The title of the button.
    """
    id: str
    title: str

    def to_dict(self) -> dict:
        return {"type": "reply", "reply": {"id": self.id, "title": self.title}}


@dataclass(frozen=True, slots=True)
class SectionRow:
    """
    Represents a row in a section.

    Attributes:
        id: The ID of the row (You get this ID when the user clicks on the row).
        title: The title of the row.
        description: The description of the row (optional).
    """
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
        button_title: The title of the button that opens the section list.
        sections: The sections in the section list (at least 1, no more than 10).
    """
    button_title: str
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "button": self.button_title,
            "sections": [section.to_dict() for section in self.sections]
        }


@dataclass(frozen=True, slots=True)
class User:
    """
    Represents a WhatsApp user.

    Attributes:
        wa_id: The WhatsApp ID of the user (The phone number with the country code).
        name: The name of the user.
    """
    wa_id: str
    name: str


class MessageType(str, Enum):
    """Message types."""
    AUDIO = "audio"
    DOCUMENT = "document"
    TEXT = "text"
    IMAGE = "image"
    INTERACTIVE = "interactive"
    STICKER = "sticker"
    VIDEO = "video"
    REACTION = "reaction"
    LOCATION = "location"
    UNSUPPORTED = "unsupported"

    # CONTACTS = "contacts"
    # SYSTEM = "system"
    # ORDER = "order"

    @classmethod
    def _missing_(cls, value):
        return cls.UNSUPPORTED

    def __str__(self):
        return self.value


@dataclass(frozen=True, slots=True)
class MediaBase:
    id: str
    sha256: str
    mime_type: str

    @classmethod
    def from_dict(cls, data: dict | None):
        return cls(**data) if data else None


@dataclass(frozen=True, slots=True)
class Image(MediaBase):
    """
    Represents an image.

    Attributes:
        id: The ID of the image.
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """
    pass


@dataclass(frozen=True, slots=True)
class Video(MediaBase):
    """
    Represents a video.

    Attributes:
        id: The ID of the video.
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """
    pass


@dataclass(frozen=True, slots=True)
class Sticker(MediaBase):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the sticker.
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """
    animated: bool


@dataclass(frozen=True, slots=True)
class Document(MediaBase):
    """
    Represents a document.

    Attributes:
        id: The ID of the document.
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """
    filename: str | None = None


@dataclass(frozen=True, slots=True)
class Audio(MediaBase):
    """
    Represents an audio.

    Attributes:
        id: The ID of the audio.
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """
    voice: bool


@dataclass(frozen=True, slots=True)
class Reaction:
    """
    Represents a reaction to a message.

    Attributes:
        message_id: The ID of the message that was reacted to.
        emoji: The emoji that was used to react to the message.
    """
    message_id: str
    emoji: str

    @classmethod
    def from_dict(cls, data: dict | None):
        return cls(**data) if data else None


@dataclass(frozen=True, slots=True)
class Location:
    """
    Represents a location.

    Attributes:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        name: The name of the location (optional).
        address: The address of the location (optional).
        url: The URL of the location (optional).
    """
    latitude: float
    longitude: float
    name: str | None = None
    address: str | None = None
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict | None):
        return cls(**data) if data else None


@dataclass(frozen=True, slots=True)
class ReplyToMessage:
    """
    Represents a message that was replied to.

    Attributes:
        message_id: The ID of the message that was replied to.
        from_user_id: The ID of the user who sent the message that was replied to.
    """
    message_id: str
    from_user_id: str

    @classmethod
    def from_dict(cls, data: dict | None):
        return cls(
            message_id=data['id'],
            from_user_id=data['from']
        ) if data else None


@dataclass(frozen=True, slots=True)
class Metadata:
    """
    Represents the metadata of a message.

    Attributes:
        display_phone_number: The phone number to which the message was sent.
        phone_number_id: The ID of the phone number to which the message was sent.
    """
    display_phone_number: str
    phone_number_id: str


@dataclass(frozen=True, slots=True)
class Message:
    """
    A message received from a user.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#messages-object

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (text, image, video, etc).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this message is a reply to. (optional)
        text: The text of the message (if the message type is text). (optional)
        image: The image of the message (if the message type is image). (optional)
        video: The video of the message (if the message type is video). (optional)
        sticker: The sticker of the message (if the message type is sticker). (optional)
        document: The document of the message (if the message type is document). (optional)
        audio: The audio of the message (if the message type is audio). (optional)
        reaction: The reaction of the message (if the message type is reaction). (optional)
        location: The location of the message (if the message type is location). (optional)
    """
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime
    type: MessageType
    reply_to_message: ReplyToMessage | None
    text: str | None
    image: Image | None
    video: Video | None
    sticker: Sticker | None
    document: Document | None
    audio: Audio | None
    reaction: Reaction | None
    location: Location | None

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        value = data['entry'][0]['changes'][0]['value']
        message = value['messages'][0]
        msg_type = MessageType(message['type'])
        user = value['contacts'][0]
        if msg_type == MessageType.UNSUPPORTED:
            raise WhatsAppError(error=message['errors'][0])
        return cls(
            _client=client,
            id=message['id'],
            type=msg_type,
            from_user=User(wa_id=user['wa_id'], name=user['profile']['name']),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            metadata=Metadata(**value['metadata']),
            reply_to_message=ReplyToMessage.from_dict(message.get('context')),
            text=message['text']['body'] if 'text' in message else None,
            image=Image.from_dict(message.get('image')),
            video=Video.from_dict(message.get('video')),
            sticker=Sticker.from_dict(message.get('sticker')),
            document=Document.from_dict(message.get('document')),
            audio=Audio.from_dict(message.get('audio')),
            reaction=Reaction.from_dict(message.get('reaction')),
            location=Location.from_dict(message.get('location'))
        )


@dataclass(frozen=True, slots=True)
class CallbackButtonReply:
    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime
    callback_id: str
    callback_title: str

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CallbackListReply:
    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime
    callback_id: str
    callback_title: str
    callback_description: str | None

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        raise NotImplementedError


class MessageStatusType(Enum):
    """Message status type."""
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'


@dataclass(frozen=True, slots=True)
class MessageStatus:
    """
    Represents the status of a message.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        recipient_id: The ID of the recipient of the message.
        conversation_id: The ID of the conversation of the message.
        expiration_timestamp: The timestamp when the conversation will expire.
    """
    id: str
    metadata: Metadata
    status: MessageStatusType
    timestamp: datetime
    recipient_id: str
    conversation_id: str
    expiration_timestamp: datetime

    @classmethod
    def from_dict(cls, data: dict):
        value = data['entry'][0]['changes'][0]['value']
        return cls(
            id=value['id'],
            metadata=Metadata(**value['metadata']),
            status=MessageStatusType(value['status']),
            timestamp=datetime.fromtimestamp(int(value['timestamp'])),
            recipient_id=value['recipient_id'],
            conversation_id=value['conversation']['id'],
            expiration_timestamp=datetime.fromtimestamp(int(value['conversation']['expiration_timestamp'])),
        )
