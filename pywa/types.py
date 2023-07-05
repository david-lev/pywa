from __future__ import annotations

__all__ = (
    "Message",
    "Contact",
    "MessageType",
    "MessageStatus",
    "MessageStatusType",
    "CallbackButton",
    "CallbackSelection",
    "InlineButton",
    "SectionRow",
    "Section",
    "SectionList",
    "MediaUrlResponse"
)

from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import TYPE_CHECKING, Iterable
from pywa import utils
from pywa.errors import WhatsAppApiError

if TYPE_CHECKING:
    from pywa.client import WhatsApp


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
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    MESSAGE_STATUS = "message_status"  # Not a real message type, used for MessageStatus
    UNSUPPORTED = "unsupported"

    # SYSTEM = "system"
    # ORDER = "order"

    @classmethod
    def _missing_(cls, value):
        return cls.UNSUPPORTED

    def __str__(self):
        return self.value


@dataclass(frozen=True, slots=True)
class MediaBase:
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    sha256: str
    mime_type: str

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict | None):
        return cls(_client=client, **data) if data else None

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return self._client.get_media_url(media_id=self.id).url

    def download(
            self,
            path: str | None = None,
            filename: str | None = None,
            in_memory: bool = False,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.
            - Same as ``WhatsApp.download_media(media_url=WhatsApp.get_media_url(media_id))``

        >>> message.image.download()

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(
            url=self.get_media_url(),
            path=path,
            filename=filename,
            in_memory=in_memory
        )


@dataclass(frozen=True, slots=True)
class Image(MediaBase):
    """
    Represents an image.

    Attributes:
        id: The ID of the image.
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
        caption: The caption of the image (optional).
    """
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class Video(MediaBase):
    """
    Represents a video.

    Attributes:
        id: The ID of the video.
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """
    caption: str | None = None


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
    caption: str | None = None


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
        emoji: The emoji that was used to react to the message (optional, ``None`` if removed).
    """
    message_id: str
    emoji: str | None = None

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

    def in_radius(self, other: Location, radius: float | int) -> bool:
        """
        Check if the location is in a radius of another location.

        Args:
            other: The other location (the center. No need for name, address or url).
            radius: The radius in kilometers.
        """
        return utils.get_distance(
            lat1=self.latitude, lon1=self.longitude, lat2=other.latitude, lon2=other.longitude
        ) <= radius


@dataclass(frozen=True, slots=True)
class MediaUrlResponse:
    """
    Represents a media response.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    url: str
    mime_type: str
    sha256: str
    file_size: int

    def download(
            self,
            filepath: str | None = None,
            filename: str | None = None,
            in_memory: bool = False,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(url=self.url, path=filepath, filename=filename, in_memory=in_memory)


@dataclass(frozen=True, slots=True)
class Contact:
    """
    Represents a contact.

    Attributes:
        name: The name of the contact.
        birthday: The birthday of the contact (in ``YYYY-MM-DD`` format, optional).
        phones: The phone numbers of the contact.
        emails: The email addresses of the contact.
        urls: The URLs of the contact.
        addresses: The addresses of the contact.
        org: The organization of the contact (optional).
    """
    name: Name
    birthday: str | None = None
    phones: list[Phone] = field(default_factory=list)
    emails: list[Email] = field(default_factory=list)
    urls: list[Url] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    org: Org | None = None

    @classmethod
    def from_dict(cls, data: dict | None):
        return cls(
            name=cls.Name(**data["name"]),
            birthday=data.get("birthday"),
            phones=[cls.Phone.from_dict(phone) for phone in data.get("phones", ())],
            emails=[cls.Email.from_dict(email) for email in data.get("emails", ())],
            urls=[cls.Url.from_dict(url) for url in data.get("urls", ())],
            addresses=[cls.Address.from_dict(address) for address in data.get("addresses", ())],
            org=cls.Org.from_dict(data.get("org")),
        ) if data else None

    def to_dict(self) -> dict:
        return {
            "name": asdict(self.name),
            "birthday": self.birthday,
            "phones": [asdict(phone) for phone in self.phones],
            "emails": [asdict(email) for email in self.emails],
            "urls": [asdict(url) for url in self.urls],
            "addresses": [asdict(address) for address in self.addresses],
            "org": asdict(self.org) if self.org else None,
        }

    @dataclass(frozen=True, slots=True)
    class Name:
        """
        Represents a contact's name.

        - At least one of the optional parameters needs to be included along with the formatted_name parameter.

        Attributes:
            formatted_name: The formatted name of the contact.
            first_name: The first name of the contact (optional).
            last_name: The last name of the contact (optional).
            middle_name: The middle name of the contact (optional).
            suffix: The suffix of the contact (optional).
            prefix: The prefix of the contact (optional).
        """
        formatted_name: str
        first_name: str | None = None
        last_name: str | None = None
        middle_name: str | None = None
        suffix: str | None = None
        prefix: str | None = None

    @dataclass(frozen=True, slots=True)
    class Phone:
        """
        Represents a contact's phone number.

        Attributes:
            phone: The phone number (If ``wa_id`` is provided, No need for the ``phone``).
            type: The type of the phone number (Standard Values are CELL, MAIN, IPHONE, HOME, and WORK. optional).
            wa_id: The WhatsApp ID of the contact (optional).
        """
        phone: str | None = None
        type: str | None = None
        wa_id: str | None = None

        @classmethod
        def from_dict(cls, data: dict | None):
            return cls(**data) if data else None

    @dataclass(frozen=True, slots=True)
    class Email:
        """
        Represents a contact's email address.

        Attributes:
            email: The email address.
            type: The type of the email address (Standard Values are WORK and HOME. optional).
        """
        email: str | None = None
        type: str | None = None

        @classmethod
        def from_dict(cls, data: dict | None):
            return cls(**data) if data else None

    @dataclass(frozen=True, slots=True)
    class Url:
        """
        Represents a contact's URL.

        Attributes:
            url: The URL.
            type: The type of the URL (Standard Values are WORK and HOME. optional).
        """
        url: str | None = None
        type: str | None = None

        @classmethod
        def from_dict(cls, data: dict | None):
            return cls(**data) if data else None

    @dataclass(frozen=True, slots=True)
    class Org:
        """
        Represents a contact's organization.

        Attributes:
            company: The company of the contact (optional).
            department: The department of the contact (optional).
            title: The title of the business contact (optional).
        """
        company: str | None = None
        department: str | None = None
        title: str | None = None

        @classmethod
        def from_dict(cls, data: dict | None):
            return cls(**data) if data else None

    @dataclass(frozen=True, slots=True)
    class Address:
        """
        Represents a contact's address.

        Attributes:
            street: The street number and name of the address (optional).
            city: The city name of the address (optional).
            state: State abbreviation.
            zip: Zip code of the address (optional).
            country: Full country name.
            country_code: Two-letter country abbreviation (e.g. US, GB, IN. optional).
            type: The type of the address (Standard Values are WORK and HOME. optional).
        """
        street: str | None = None
        city: str | None = None
        state: str | None = None
        zip: str | None = None
        country: str | None = None
        country_code: str | None = None
        type: str | None = None

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
        ) if (data and 'id' in data) else None


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
    """Base class for all update types."""
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime

    @property
    def sender(self) -> str:
        return self.from_user.wa_id

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to."""
        return self.id

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
            header: The header of the message (if keyboard is provided, optional, up to 60 characters, no markdown allowed).
            footer: The footer of the message (if keyboard is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_message(
            to=self.sender,
            text=text,
            preview_url=preview_url,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            keyboard=keyboard,
            header=header,
            footer=footer
        )

    reply = reply_text  # alias

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
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_image(
            to=self.sender,
            image=image,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
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
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_video(
            to=self.sender,
            video=video,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
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
            filename: The filename of the document (optional, The extension of the filename will specify what format the document is displayed as in WhatsApp).
            caption: The caption of the document (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_document(
            to=self.sender,
            document=document,
            filename=filename,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
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
            reply_to_message_id=self.message_id_to_reply if quote else None
        )

    def reply_sticker(
            self,
            sticker: str | bytes,
            quote: bool = False,
    ) -> str:
        """
        Reply to the message with a sticker.

        Args:
            sticker: The sticker to reply with.
            quote: Whether to quote the message (default: False).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_sticker(
            to=self.sender,
            sticker=sticker,
            reply_to_message_id=self.message_id_to_reply if quote else None
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

    def reply_contact(
            self,
            contact: Contact | Iterable[Contact],
            quote: bool = False,
    ) -> str:
        """
        Reply to the message with a contact.

        Args:
            contact: The contact/s to send.
            quote: Whether to quote the message (default: False).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_contact(
            to=self.sender,
            contact=contact,
            reply_to_message_id=self.message_id_to_reply if quote else None
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
            message_id=self.message_id_to_reply
        )

    def unreact(
            self,
    ) -> str:
        """
        Remove the reaction from the message.

        Returns:
            The ID of the sent message.
        """
        return self._client.remove_reaction(
            to=self.sender,
            message_id=self.message_id_to_reply
        )

    def mark_as_read(
            self
    ) -> bool:
        """
        Mark the message as read.

        Returns:
            Whether it was successful.
        """
        return self._client.mark_message_as_read(
            message_id=self.message_id_to_reply
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
        forwarded: Whether the message was forwarded.
        forwarded_frequently: When the message was been forwarded meny times.
        text: The text of the message (if the message type is text). (optional)
        image: The image of the message (if the message type is image). (optional)
        video: The video of the message (if the message type is video). (optional)
        sticker: The sticker of the message (if the message type is sticker). (optional)
        document: The document of the message (if the message type is document). (optional)
        audio: The audio of the message (if the message type is audio). (optional)
        reaction: The reaction of the message (if the message type is reaction). (optional)
        location: The location of the message (if the message type is location). (optional)
        contacts: The contacts of the message (if the message type is contacts). (optional)
    """
    reply_to_message: ReplyToMessage | None
    forwarded: bool
    forwarded_frequently: bool
    text: str | None
    image: Image | None
    video: Video | None
    sticker: Sticker | None
    document: Document | None
    audio: Audio | None
    reaction: Reaction | None
    location: Location | None
    contacts: list[Contact] | None

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message"""
        return self.id if self.type != MessageType.REACTION else self.reaction.message_id

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        message = value['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            type=MessageType(message['type']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            metadata=Metadata(**value['metadata']),
            forwarded=message.get('context', {}).get('forwarded', False),
            forwarded_frequently=message.get('context', {}).get('frequently_forwarded', False),
            reply_to_message=ReplyToMessage.from_dict(message.get('context')),
            text=message['text']['body'] if 'text' in message else None,
            image=Image.from_dict(client=client, data=message.get('image')),
            video=Video.from_dict(client=client, data=message.get('video')),
            sticker=Sticker.from_dict(client=client, data=message.get('sticker')),
            document=Document.from_dict(client=client, data=message.get('document')),
            audio=Audio.from_dict(client=client, data=message.get('audio')),
            reaction=Reaction.from_dict(message.get('reaction')),
            location=Location.from_dict(message.get('location')),
            contacts=[Contact.from_dict(contact) for contact in message.get('contacts', ())] or None
        )

    def download_media(
            self,
            filepath: str | None = None,
            filename: str | None = None,
            in_memory: bool = False,
    ) -> str | bytes:
        """
        Download a media file from WhatsApp servers (image, video, sticker, document or audio).

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.

        Raises:
            ValueError: If the message does not contain any media.
        """
        media = self.image or self.video or self.sticker or self.document or self.audio
        if not media:
            raise ValueError('The message does not contain any media.')
        return media.download(path=filepath, filename=filename, in_memory=in_memory)


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
            metadata=Metadata(**value['metadata']),
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
            metadata=Metadata(**value['metadata']),
            type=MessageType(message['type']),
            from_user=User.from_dict(value['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            reply_to_message=ReplyToMessage.from_dict(message['context']),
            data=message['interactive']['list_reply']['id'],
            title=message['interactive']['list_reply']['title'],
            description=message['interactive']['list_reply'].get('description')
        )


class MessageStatusType(Enum):
    """Message status type."""
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'


@dataclass(frozen=True, slots=True)
class MessageStatus(BaseUpdate):
    """
    Represents the status of a message.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object

    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always ``message_status``).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        from_user: The user who the message was sent to.
        error: The error that occurred (if status is ``failed``).
    """
    status: MessageStatusType
    error: WhatsAppApiError | None

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        status = value['statuses'][0]
        status_type = MessageStatusType(status['status'])
        return cls(
            _client=client,
            id=status['id'],
            metadata=Metadata(**value['metadata']),
            type=MessageType.MESSAGE_STATUS,
            status=status_type,
            timestamp=datetime.fromtimestamp(int(status['timestamp'])),
            from_user=User(wa_id=status['recipient_id'], name=None),
            error=WhatsAppApiError.from_incoming_error(status['errors'][0])
            if status_type == MessageStatusType.FAILED else None
        )
