from __future__ import annotations

__all__ = (
    "Message",
    "MessageType",
    "MessageStatus",
    "MessageStatusType",
    "CallbackButton",
    "CallbackSelection",
    "InlineButton",
    "SectionRow",
    "Section",
    "SectionList",
)

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pywa.client import WhatsApp


@dataclass(frozen=True, slots=True)
class InlineButton:
    """
    Represents an inline button in a keyboard.

    Attributes:
        title: The title of the button.
        callback_data: The payload to send when the user clicks on the button.
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
        title: The title of the row.
        callback_data: The payload to send when the user clicks on the row.
        description: The description of the row (optional).
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
        name: The name of the user (``None`` on MessageStatus).
    """
    wa_id: str
    name: str | None

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(wa_id=data["wa_id"], name=data["profile"]["name"])


class MessageType(str, Enum):
    """Message types."""
    AUDIO = "audio"
    DOCUMENT = "document"
    TEXT = "text"
    IMAGE = "image"
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
class BaseUpdate:
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime

    @property
    def sender(self) -> str:
        return self.from_user.wa_id

    def reply_text(
            self,
            text: str,
            preview_url: bool = False,
            quote: bool = False,
            keyboard: list[InlineButton] | SectionList | None = None,
            header: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with text.

        Args:
            text: The text to reply with.
            preview_url: Whether to show a preview of the URL in the text (default: False).
            quote: Whether to quote the message (default: False).
            keyboard: The keyboard to send with the message (optional).
            header: The header of the message (if keyboard is provided, optional).
            footer: The footer of the message (if keyboard is provided, optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_message(
            to=self.sender,
            text=text,
            preview_url=preview_url,
            reply_to_message_id=self.id if quote else None,
            keyboard=keyboard,
            header=header,
            footer=footer
        )

    def reply_image(
            self,
            image: str | bytes,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with an image.

        Args:
            image: The image to reply with.
            caption: The caption of the image (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_image(
            to=self.sender,
            image=image,
            caption=caption,
            reply_to_message_id=self.id if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_video(
            self,
            video: str | bytes,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with a video.

        Args:
            video: The video to reply with.
            caption: The caption of the video (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_video(
            to=self.sender,
            video=video,
            caption=caption,
            reply_to_message_id=self.id if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_document(
            self,
            document: str | bytes,
            filename: str | None = None,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with a document.

        Args:
            document: The document to reply with.
            filename: The filename of the document (optional).
            caption: The caption of the document (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_document(
            to=self.sender,
            document=document,
            filename=filename,
            caption=caption,
            reply_to_message_id=self.id if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_audio(
            self,
            audio: str | bytes,
            quote: bool = False,
    ) -> str:
        """
        Reply to the message with an audio.

        Args:
            audio: The audio to reply with.
            quote: Whether to quote the message (default: False).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_audio(
            to=self.sender,
            audio=audio,
            reply_to_message_id=self.id if quote else None
        )

    def reply_sticker(
            self,
            sticker: str | bytes,
            animated: bool = False,
            quote: bool = False,
    ) -> str:
        """
        Reply to the message with a sticker.

        Args:
            sticker: The sticker to reply with.
            animated: Whether the sticker is animated (default: False).
            quote: Whether to quote the message (default: False).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_sticker(
            to=self.sender,
            sticker=sticker,
            animated=animated,
            reply_to_message_id=self.id if quote else None
        )

    def reply_location(
            self,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ) -> str:
        """
        Reply to the message with a location.

        Args:
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location (optional).
            address: The address of the location (optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_location(
            to=self.sender,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address
        )

    def react(
            self,
            emoji: str,
    ) -> str:
        """
        React to the message with an emoji.

        Args:
            emoji: The emoji to react with.

        Returns:
            The ID of the sent message.
        """
        return self._client.send_reaction(
            to=self.sender,
            emoji=emoji,
            message_id=self.id
        )


@dataclass(frozen=True, slots=True)
class Message(BaseUpdate):
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
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        msg_type = MessageType(message['type'])
        return cls(
            _client=client,
            id=message['id'],
            type=msg_type,
            from_user=User.from_dict(value['contacts'][0]),
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
class CallbackButton(BaseUpdate):
    """
    Represents a callback button.

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        data: The data of the button.
        title: The title of the button.
    """
    data: str
    title: str

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata(**value['metadata']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
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
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        data: The data of the selection.
        title: The title of the selection.
        description: The description of the selection (optional).
    """
    data: str
    title: str
    description: str | None

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata(**value['metadata']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            data=message['interactive']['list_reply']['id'],
            title=message['interactive']['list_reply']['title'],
            description=message['interactive']['list_reply'].get('description')
        )


class MessageStatusType(Enum):
    """Message status type."""
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class MessageStatus(BaseUpdate):
    """
    Represents the status of a message.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        from_user: The user who the message was sent to.
    """
    status: MessageStatusType

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        status = value['statuses'][0]
        return cls(
            _client=client,
            id=status['id'],
            metadata=Metadata(**value['metadata']),
            status=MessageStatusType(status['status']),
            timestamp=datetime.fromtimestamp(int(status['timestamp'])),
            from_user=User(wa_id=status['recipient_id'], name=None)
        )
