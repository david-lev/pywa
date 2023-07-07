from __future__ import annotations
from dataclasses import dataclass, fields, field, asdict
from enum import Enum
from typing import TYPE_CHECKING
from pywa import utils

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class _StrEnum(str, Enum):
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other.lower()
        return super().__eq__(other)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass(frozen=True, slots=True, kw_only=True)
class _FromDict:
    """Base class for dataclasses that can be created from dict unpacking."""

    # noinspection PyArgumentList
    @classmethod
    def from_dict(cls, **kwargs):
        return cls(**{
            k: v for k, v in kwargs.items()
            if k in (f.name for f in fields(cls))
        })


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


class MessageType(_StrEnum):
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


@dataclass(frozen=True, slots=True)
class Reaction(_FromDict):
    """
    Represents a reaction to a message.

    Attributes:
        message_id: The ID of the message that was reacted to.
        emoji: The emoji that was used to react to the message (optional, ``None`` if removed).
    """
    message_id: str
    emoji: str | None = None


@dataclass(frozen=True, slots=True)
class Location(_FromDict):
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

    def in_radius(self, lat: float, lon: float, radius: float | int) -> bool:
        """
        Check if the location is in a radius of another location.

        Args:
            lat: The latitude of the other location.
            lon: The longitude of the other location.
            radius: The radius in kilometers.
        """
        return utils.get_distance(lat1=self.latitude, lon1=self.longitude, lat2=lat, lon2=lon) <= radius


@dataclass(frozen=True, slots=True)
class MediaUrlResponse(_FromDict):
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
    def from_dict(cls, **data):
        return cls(
            name=cls.Name.from_dict(**data["name"]),
            birthday=data.get("birthday"),
            phones=[cls.Phone.from_dict(**phone) for phone in data.get("phones", ())],
            emails=[cls.Email.from_dict(**email) for email in data.get("emails", ())],
            urls=[cls.Url.from_dict(**url) for url in data.get("urls", ())],
            addresses=[cls.Address.from_dict(**address) for address in data.get("addresses", ())],
            org=cls.Org.from_dict(**data.get("org")) if data.get("org") else None,
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
    class Name(_FromDict):
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
    class Phone(_FromDict):
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

    @dataclass(frozen=True, slots=True)
    class Email(_FromDict):
        """
        Represents a contact's email address.

        Attributes:
            email: The email address.
            type: The type of the email address (Standard Values are WORK and HOME. optional).
        """
        email: str | None = None
        type: str | None = None

    @dataclass(frozen=True, slots=True)
    class Url(_FromDict):
        """
        Represents a contact's URL.

        Attributes:
            url: The URL.
            type: The type of the URL (Standard Values are WORK and HOME. optional).
        """
        url: str | None = None
        type: str | None = None

    @dataclass(frozen=True, slots=True)
    class Org(_FromDict):
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

    @dataclass(frozen=True, slots=True)
    class Address(_FromDict):
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
class Metadata(_FromDict):
    """
    Represents the metadata of a message.

    Attributes:
        display_phone_number: The phone number to which the message was sent.
        phone_number_id: The ID of the phone number to which the message was sent.
    """
    display_phone_number: str
    phone_number_id: str
