from __future__ import annotations
from dataclasses import dataclass, fields, field, asdict
from enum import Enum
from typing import Iterable, TYPE_CHECKING
from pywa import utils

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class _StrEnum(str, Enum):
    def __eq__(self, other: _StrEnum | str):
        if isinstance(other, str):
            return self.value == other.lower()
        return super().__eq__(other)

    def __ne__(self, other: _StrEnum | str):
        return not self.__eq__(other)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass(frozen=True, slots=True, kw_only=True)
class _FromDict:
    """Base class for dataclasses that can be created from dict unpacking."""

    # noinspection PyArgumentList
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        data.update(kwargs)
        return cls(**{
            k: v for k, v in data.items()
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

    def as_vcard(self) -> str:
        """Get the user as a vCard."""
        return "\n".join((
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{self.name}",
            f"TEL;type=CELL;type=VOICE:+{self.wa_id}",
            "END:VCARD"
        ))


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
    ORDER = "order"
    SYSTEM = "system"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

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
    phones: Iterable[Phone] = field(default_factory=tuple)
    emails: Iterable[Email] = field(default_factory=tuple)
    urls: Iterable[Url] = field(default_factory=tuple)
    addresses: Iterable[Address] = field(default_factory=tuple)
    org: Org | None = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=cls.Name.from_dict(data["name"]),
            birthday=data.get("birthday"),
            phones=tuple(cls.Phone.from_dict(phone) for phone in data.get("phones", ())),
            emails=tuple(cls.Email.from_dict(email) for email in data.get("emails", ())),
            urls=tuple(cls.Url.from_dict(url) for url in data.get("urls", ())),
            addresses=tuple(cls.Address.from_dict(address) for address in data.get("addresses", ())),
            org=cls.Org.from_dict(data["org"]) if "org" in data else None
        )

    def to_dict(self) -> dict[str, str | dict[str, str] | list[dict[str, str]] | None]:
        """Get the contact as a dict."""
        return {
            "name": asdict(self.name),
            "birthday": self.birthday,
            "phones": [asdict(phone) for phone in self.phones],
            "emails": [asdict(email) for email in self.emails],
            "urls": [asdict(url) for url in self.urls],
            "addresses": [asdict(address) for address in self.addresses],
            "org": asdict(self.org) if self.org else None,
        }

    def as_vcard(self) -> str:
        """Get the contact as a vCard."""
        return "\n".join(s for s in (
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{self.name.formatted_name}",
            f"BDAY:{self.birthday}" if self.birthday else None,
            "\n".join(f"TEL;type={phone.type}:{phone.phone}" for phone in self.phones) if self.phones else None,
            "\n".join(f"EMAIL;type={email.type}:{email.email}" for email in self.emails) if self.emails else None,
            "\n".join(f"URL;type={url.type}:{url.url}" for url in self.urls) if self.urls else None,
            "\n".join(f"ADR;type={a.type}:;;{';'.join((getattr(a, f) or '') for f in ('street', 'city', 'state', 'zip', 'country') )}"
                      for a in self.addresses) if self.addresses else None,
            "END:VCARD"
        ) if s is not None)

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
    def from_dict(cls, data: dict | None) -> ReplyToMessage | None:
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


@dataclass(frozen=True, slots=True)
class Product:
    """
    Represents a product in an order.

    Attributes:
        sku: Unique identifier of the product in a catalog (also referred to as `Content ID` or `Retailer ID`).
        quantity: Number of items ordered.
        price: Price of the item.
        currency: Currency of the price.
    """
    sku: str
    quantity: int
    price: float
    currency: str

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        return cls(
            sku=data["product_retailer_id"],
            quantity=data["quantity"],
            price=data["item_price"],
            currency=data["currency"]
        )

    @property
    def total_price(self) -> float:
        """Total price of the product."""
        return self.quantity * self.price


@dataclass(frozen=True, slots=True)
class Order:
    """
    Represents an order.

    Attributes:
        catalog_id: The ID for the catalog the ordered item belongs to.
        products:The ordered products.
        text: Text message from the user sent along with the order (optional).

    Properties:
        total_price: Total price of the order.
    """
    catalog_id: str
    products: tuple[Product]
    text: str | None

    @classmethod
    def from_dict(cls, data: dict, _client: WhatsApp) -> Order:
        return cls(
            catalog_id=data['catalog_id'],
            text=data.get('text'),
            products=tuple(Product.from_dict(p) for p in data['product_items'])
        )

    @property
    def total_price(self) -> float:
        """Total price of the order."""
        return sum(p.total_price for p in self.products)


@dataclass(frozen=True, slots=True)
class System:
    """
    Represents a system update (A customer has updated their phone number or profile information).

    Attributes:
        type: The type of the system update (customer_changed_number or customer_identity_changed).
        body: Describes the change to the customer's identity or phone number.
        identity: Hash for the identity fetched from server.
        wa_id: The WhatsApp ID for the customer prior to the update.
        new_wa_id: New WhatsApp ID for the customer when their phone number is updated.
    """
    type: str
    body: str
    identity: str
    wa_id: str
    new_wa_id: str | None

    @classmethod
    def from_dict(cls, data: dict, _client: WhatsApp) -> System:
        return cls(
            type=data['type'],
            body=data['body'],
            identity=data['identity'],
            wa_id=data['customer'],
            new_wa_id=data.get('wa_id')
        )
