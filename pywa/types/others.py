from __future__ import annotations

"""Types for other objects."""

import dataclasses
import importlib
import logging
from typing import TYPE_CHECKING, Any, Iterable

from pywa import utils

if TYPE_CHECKING:
    from message_status import MessageStatus
    from media import Image, Video, Document, Audio, Sticker
    from callback import CallbackButton, CallbackSelection
    from pywa.client import WhatsApp

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True)
class User:
    """
    Represents a WhatsApp user.

    Attributes:
        wa_id: The WhatsApp ID of the user (The phone number with the country code).
        name: The name of the user (``None`` on :class:`MessageStatus`).
    """

    wa_id: str
    name: str | None

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(wa_id=data["wa_id"], name=data["profile"]["name"])

    def as_vcard(self) -> str:
        """Get the user as a vCard."""
        return "\n".join(
            (
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{self.name}",
                f"TEL;type=CELL;type=VOICE:+{self.wa_id}",
                "END:VCARD",
            )
        )


class MessageType(utils.StrEnum):
    """
    Message types.

    Attributes:
        TEXT: Message.text -> :class:`str`.
        IMAGE: Message.image -> :class:`Image`.
        VIDEO: Message.video -> :class:`Video`.
        DOCUMENT: Message.document -> :class:`Document`.
        AUDIO: Message.audio -> :class:`Audio`.
        STICKER: Message.sticker -> :class:`Sticker`.
        REACTION: Message.reaction -> :class:`Reaction`.
        LOCATION: Message.location -> :class:`Location`.
        CONTACTS: Message.contacts -> tuple[:class:`Contact`].
        ORDER: Message.order -> :class:`Order`.
        SYSTEM: Message.system -> :class:`System`.
        UNKNOWN: An unknown message (Warning with the actual type will be logged).
        UNSUPPORTED: An unsupported message (message type not supported by WhatsApp Cloud API).
        INTERACTIVE: Only used in :class:`CallbackButton` and :class:`CallbackSelection`.
        BUTTON: Only used in :class:`CallbackButton`.
        REQUEST_WELCOME: Only used in :class:`ChatOpened`.
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    STICKER = "sticker"
    REACTION = "reaction"
    LOCATION = "location"
    CONTACTS = "contacts"
    ORDER = "order"
    SYSTEM = "system"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

    INTERACTIVE = "interactive"
    BUTTON = "button"
    REQUEST_WELCOME = "request_welcome"

    @classmethod
    def _missing_(cls, value: str) -> MessageType:
        _logger.warning(f"Unknown message type: {value}")
        return cls.UNKNOWN


@dataclasses.dataclass(frozen=True, slots=True)
class Reaction(utils.FromDict):
    """
    Represents a reaction to a message.

    Attributes:
        message_id: The ID of the message that was reacted to.
        emoji: The emoji that was used to react to the message (optional, ``None`` if removed).
    """

    message_id: str
    emoji: str | None = None

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> Reaction:
        return cls(
            message_id=data["message_id"], emoji=data.get("emoji") or None
        )  # sometimes it's empty string 🤦‍

    @property
    def is_removed(self) -> bool:
        """Check if the reaction is removed."""
        return self.emoji is None


@dataclasses.dataclass(frozen=True, slots=True)
class Location(utils.FromDict):
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

    @property
    def current_location(self) -> bool:
        """Check if the shared location is the current location or manually selected."""
        return not any((self.name, self.address, self.url))

    def in_radius(self, lat: float, lon: float, radius: float | int) -> bool:
        """
        Check if the location is in a radius of another location.

        Args:
            lat: The latitude of the other location.
            lon: The longitude of the other location.
            radius: The radius in kilometers.
        """
        math = importlib.import_module("math")
        lon1, lat1, lon2, lat2 = map(
            math.radians, [self.longitude, self.latitude, lon, lat]
        )
        return (
            (
                2
                * math.asin(
                    math.sqrt(
                        math.sin((lat2 - lat1) / 2) ** 2
                        + math.cos(lat1)
                        * math.cos(lat2)
                        * math.sin((lon2 - lon1) / 2) ** 2
                    )
                )
            )
            * 6371
        ) <= radius


@dataclasses.dataclass(slots=True)
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
    phones: Iterable[Phone] = dataclasses.field(default_factory=tuple)
    emails: Iterable[Email] = dataclasses.field(default_factory=tuple)
    urls: Iterable[Url] = dataclasses.field(default_factory=tuple)
    addresses: Iterable[Address] = dataclasses.field(default_factory=tuple)
    org: Org | None = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=cls.Name.from_dict(data["name"]),
            birthday=data.get("birthday"),
            phones=tuple(
                cls.Phone.from_dict(phone) for phone in data.get("phones", ())
            ),
            emails=tuple(
                cls.Email.from_dict(email) for email in data.get("emails", ())
            ),
            urls=tuple(cls.Url.from_dict(url) for url in data.get("urls", ())),
            addresses=tuple(
                cls.Address.from_dict(address) for address in data.get("addresses", ())
            ),
            org=cls.Org.from_dict(data["org"]) if "org" in data else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Get the contact as a dict."""
        return {
            "name": dataclasses.asdict(self.name),
            "birthday": self.birthday,
            "phones": tuple(dataclasses.asdict(phone) for phone in self.phones),
            "emails": tuple(dataclasses.asdict(email) for email in self.emails),
            "urls": tuple(dataclasses.asdict(url) for url in self.urls),
            "addresses": tuple(
                dataclasses.asdict(address) for address in self.addresses
            ),
            "org": dataclasses.asdict(self.org) if self.org else None,
        }

    def as_vcard(self) -> str:
        """Get the contact as a vCard."""
        return "\n".join(
            s
            for s in (
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{self.name.formatted_name}",
                f"BDAY:{self.birthday}" if self.birthday else None,
                "\n".join(
                    f"TEL;type={phone.type}:{phone.phone}" for phone in self.phones
                )
                if self.phones
                else None,
                "\n".join(
                    f"EMAIL;type={email.type}:{email.email}" for email in self.emails
                )
                if self.emails
                else None,
                "\n".join(f"URL;type={url.type}:{url.url}" for url in self.urls)
                if self.urls
                else None,
                "\n".join(
                    f"ADR;type={a.type}:;;{';'.join((getattr(a, f) or '') for f in ('street', 'city', 'state', 'zip', 'country') )}"
                    for a in self.addresses
                )
                if self.addresses
                else None,
                "END:VCARD",
            )
            if s is not None
        )

    @dataclasses.dataclass(frozen=True, slots=True)
    class Name(utils.FromDict):
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

    @dataclasses.dataclass(frozen=True, slots=True)
    class Phone(utils.FromDict):
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

    @dataclasses.dataclass(frozen=True, slots=True)
    class Email(utils.FromDict):
        """
        Represents a contact's email address.

        Attributes:
            email: The email address.
            type: The type of the email address (Standard Values are WORK and HOME. optional).
        """

        email: str | None = None
        type: str | None = None

    @dataclasses.dataclass(frozen=True, slots=True)
    class Url(utils.FromDict):
        """
        Represents a contact's URL.

        Attributes:
            url: The URL.
            type: The type of the URL (Standard Values are WORK and HOME. optional).
        """

        url: str | None = None
        type: str | None = None

    @dataclasses.dataclass(frozen=True, slots=True)
    class Org(utils.FromDict):
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

    @dataclasses.dataclass(frozen=True, slots=True)
    class Address(utils.FromDict):
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


@dataclasses.dataclass(frozen=True, slots=True)
class ReferredProduct:
    """
    Represents a product this message is referring to.

    Attributes:
        catalog_id:
        sku: Unique identifier of the product in a catalog (also referred to as ``Content ID`` or ``Retailer ID``).

    """

    catalog_id: str
    sku: str

    @classmethod
    def from_dict(cls, data: dict | None) -> ReferredProduct | None:
        return (
            cls(
                catalog_id=data["catalog_id"],
                sku=data["product_retailer_id"],
            )
            if data
            else None
        )


@dataclasses.dataclass(frozen=True, slots=True)
class ReplyToMessage:
    """
    Represents a message that was replied to.

    Attributes:
        message_id: The ID of the message that was replied to.
        from_user_id: The ID of the user who sent the message that was replied to.
        referred_product: Referred product describing the product the user is requesting information about.
    """

    message_id: str
    from_user_id: str
    referred_product: ReferredProduct | None

    @classmethod
    def from_dict(cls, data: dict | None) -> ReplyToMessage | None:
        return (
            cls(
                message_id=data["id"],
                from_user_id=data["from"],
                referred_product=ReferredProduct.from_dict(
                    data.get("referred_product")
                ),
            )
            if (data and "id" in data)
            else None
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Metadata(utils.FromDict):
    """
    Represents the metadata of a message.

    Attributes:
        display_phone_number: The phone number to which the message was sent.
        phone_number_id: The ID of the phone number to which the message was sent.
    """

    display_phone_number: str
    phone_number_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class Product:
    """
    Represents a product in an order.

    Attributes:
        sku: Unique identifier of the product in a catalog (also referred to as ``Content ID`` or ``Retailer ID``).
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
            currency=data["currency"],
        )

    @property
    def total_price(self) -> float:
        """Total price of the product."""
        return self.quantity * self.price


@dataclasses.dataclass(frozen=True, slots=True)
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
    products: tuple[Product, ...]
    text: str | None

    @classmethod
    def from_dict(cls, data: dict, _client: WhatsApp) -> Order:
        return cls(
            catalog_id=data["catalog_id"],
            text=data.get("text"),
            products=tuple(Product.from_dict(p) for p in data["product_items"]),
        )

    @property
    def total_price(self) -> float:
        """Total price of the order."""
        return sum(p.total_price for p in self.products)


@dataclasses.dataclass(frozen=True, slots=True)
class System:
    """
    Represents a system update (A customer has updated their phone number or profile information).

    Attributes:
        type: The type of the system update (``customer_changed_number`` or ``customer_identity_changed``).
        body: Describes the change to the customer's identity or phone number.
        identity: Hash for the identity fetched from server.
        wa_id: The WhatsApp ID for the customer prior to the update.
        new_wa_id: New WhatsApp ID for the customer when their phone number is updated.
    """

    type: str | None
    body: str | None
    identity: str | None
    wa_id: str | None
    new_wa_id: str | None

    @classmethod
    def from_dict(cls, data: dict, _client: WhatsApp) -> System:
        return cls(
            type=data.get("type"),
            body=data.get("body"),
            identity=data.get("identity"),
            wa_id=data.get("customer"),
            new_wa_id=data.get("wa_id"),
        )


@dataclasses.dataclass(slots=True)
class ProductsSection:
    """
    Represents a section in a section list.

    Attributes:
        title: The title of the products section (up to 24 characters).
        skus: The SKUs of the products in the section (at least 1, no more than 30).
    """

    title: str
    skus: Iterable[str]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "product_items": tuple({"product_retailer_id": sku} for sku in self.skus),
        }


class Industry(utils.StrEnum):
    """
    Represents the industry of a business.

    Attributes:
        UNDEFINED: Undefined.
        OTHER: Other.
        AUTO: Automotive.
        BEAUTY: Beauty.
        APPAREL: Apparel.
        EDU: Education.
        ENTERTAIN: Entertainment.
        EVENT_PLAN: Event planning.
        FINANCE: Finance.
        GROCERY: Grocery store.
        GOVT: Government.
        HOTEL: Hotel.
        HEALTH: Health.
        NONPROFIT: Nonprofit.
        PROF_SERVICES: Professional services.
        RETAIL: Retail.
        TRAVEL: Travel.
        RESTAURANT: Restaurant.
        NOT_A_BIZ: Not a business.
    """

    UNDEFINED = "UNDEFINED"
    OTHER = "OTHER"
    AUTO = "AUTO"
    BEAUTY = "BEAUTY"
    APPAREL = "APPAREL"
    EDU = "EDU"
    ENTERTAIN = "ENTERTAIN"
    EVENT_PLAN = "EVENT_PLAN"
    FINANCE = "FINANCE"
    GROCERY = "GROCERY"
    GOVT = "GOVT"
    HOTEL = "HOTEL"
    HEALTH = "HEALTH"
    NONPROFIT = "NONPROFIT"
    PROF_SERVICES = "PROF_SERVICES"
    RETAIL = "RETAIL"
    TRAVEL = "TRAVEL"
    RESTAURANT = "RESTAURANT"
    NOT_A_BIZ = "NOT_A_BIZ"

    @classmethod
    def _missing_(cls, value: str) -> None:
        return None


@dataclasses.dataclass(frozen=True, slots=True)
class BusinessProfile:
    """
    Represents a business profile.

    Attributes:
        about: This text appears in the business's profile, beneath its profile image, phone number, and contact buttons.
        address: Address of the business. Character limit 256.
        description: Description of the business. Character limit 512.
        email: The contact email address (in valid email format) of the business. Character limit 128.
        industry: The industry of the business.
        profile_picture_url: URL of the profile picture that was uploaded to Meta.
        websites: The URLs associated with the business. For instance, a website, Facebook Page, or Instagram.
         There is a maximum of 2 websites with a maximum of 256 characters each.
    """

    about: str
    address: str | None
    industry: Industry
    description: str | None
    email: str | None
    profile_picture_url: str | None
    websites: tuple[str, ...] | None

    @classmethod
    def from_dict(cls, data: dict) -> BusinessProfile:
        return cls(
            about=data["about"],
            address=data.get("address"),
            industry=Industry(data["vertical"]),
            description=data.get("description"),
            email=data.get("email"),
            profile_picture_url=data.get("profile_picture_url"),
            websites=tuple(data.get("websites", [])) or None,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class CommerceSettings:
    """
    Represents the WhatsApp commerce settings.

    Attributes:
        catalog_id: The ID of the catalog associated with the business.
        is_catalog_visible: Whether the catalog is visible to customers.
        is_cart_enabled: Whether the cart is enabled.
    """

    catalog_id: str
    is_catalog_visible: bool
    is_cart_enabled: bool

    @classmethod
    def from_dict(cls, data: dict) -> CommerceSettings:
        return cls(
            catalog_id=data["id"],
            is_catalog_visible=data["is_catalog_visible"],
            is_cart_enabled=data["is_cart_enabled"],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class WhatsAppBusinessAccount(utils.FromDict):
    """
    Represents a WhatsApp Business Account.

    Attributes:
        id: The ID of the account.
        message_template_namespace: The namespace of the message templates.
        name: The name of the account.
        timezone_id: The timezone ID of the account.
    """

    id: str
    message_template_namespace: str
    name: str
    timezone_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class FacebookApplication(utils.FromDict):
    """
    Represents a Facebook Application.

    Attributes:
        id: The ID of the application.
        name: The name of the application.
        link: The link to the application.
    """

    id: str
    name: str
    link: str
