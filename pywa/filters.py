"""
Usefully filters to use in your handlers.

>>> from pywa import WhatsApp, types, filters
>>> wa = WhatsApp(...)

>>> @wa.on_message(filters.command("start"))
... def on_hi_msg(_: WhatsApp, m: types.Message):
...     print("This is a welcome message!")
"""

from __future__ import annotations

__all__ = [
    "new",
    "true",
    "false",
    "private",
    "group",
    "update_id",
    "waba_id",
    "forwarded",
    "forwarded_many_times",
    "reply",
    "replays_to",
    "has_referred_product",
    "sent_to",
    "sent_to_me",
    "from_users",
    "without_wa_id",
    "from_countries",
    "matches",
    "contains",
    "startswith",
    "endswith",
    "regex",
    "message",
    "text",
    "is_command",
    "command",
    "media",
    "mimetypes",
    "extensions",
    "has_caption",
    "image",
    "video",
    "audio",
    "audio_only",
    "voice",
    "document",
    "sticker",
    "animated_sticker",
    "static_sticker",
    "reaction",
    "reaction_added",
    "reaction_removed",
    "reaction_emojis",
    "unsupported",
    "location",
    "current_location",
    "location_in_radius",
    "contacts",
    "contact_info_shared",
    "contacts_has_wa",
    "order",
    "callback_button",
    "callback_selection",
    "message_status",
    "sent",
    "delivered",
    "read",
    "played",
    "failed",
    "failed_with",
    "with_tracker",
    "flow_completion",
    "template_status",
    "template_status_approved",
    "template_status_rejected",
    "template_quality",
    "template_category",
    "template_components",
    "call_connect",
    "outgoing_call",
    "incoming_call",
    "call_status",
    "call_answered",
    "call_rejected",
    "call_ringing",
    "call_permission_update",
    "call_permission_accepted",
    "call_permission_rejected",
    "call_terminate",
    "phone_number_change",
    "identity_change",
    "user_marketing_preferences",
    "user_marketing_preferences_stop",
    "user_marketing_preferences_resume",
    "account_update",
    "account_deleted",
    "account_restriction",
    "account_violation",
    "ad_account_linked",
    "auth_intl_price_eligibility_update",
    "business_primary_location_country_update",
    "account_disabled",
    "partner_added",
    "partner_app_installed",
    "partner_app_uninstalled",
    "partner_client_certification_status_update",
    "partner_removed",
    "volume_based_pricing_tier_update",
    "account_offboarded",
    "account_reconnected",
]

import re
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    TypeVar,
    overload,
)

from . import _helpers as helpers
from . import types
from .errors import WhatsAppError
from .types import base_update, chat
from .types.others import ContactsOrigin

if TYPE_CHECKING:
    from pywa.client import WhatsApp

_T = TypeVar("_T", contravariant=True)
_U = TypeVar("_U", contravariant=True)
_V = TypeVar("_V")


class Filter(Generic[_T]):
    """Base filter class handling both sync and async."""

    def check_sync(self, wa: WhatsApp, update: _T) -> bool:
        raise NotImplementedError

    async def check_async(self, wa: WhatsApp, update: _T) -> bool:
        raise NotImplementedError

    def has_async(self) -> bool:
        raise NotImplementedError

    def __and__(self, other: Filter[_T]) -> Filter[_T]:
        return AndFilter(self, other)

    def __or__(self, other: Filter[_U]) -> Filter[_T | _U]:
        return OrFilter(self, other)

    def __invert__(self) -> Filter[_T]:
        return NotFilter(self)


class AndFilter(Filter[_T]):
    def __init__(self, left: Filter[_T], right: Filter[_T]):
        self.left = left
        self.right = right

    def check_sync(self, wa: WhatsApp, update: _T) -> bool:
        return self.left.check_sync(wa, update) and self.right.check_sync(wa, update)

    async def check_async(self, wa: WhatsApp, update: _T) -> bool:
        return await self.left.check_async(wa, update) and await self.right.check_async(
            wa, update
        )

    def has_async(self) -> bool:
        return self.left.has_async() or self.right.has_async()


class OrFilter(Filter[_T]):
    def __init__(self, left: Filter[Any], right: Filter[Any]):
        self.left = left
        self.right = right

    def check_sync(self, wa: WhatsApp, update: _T) -> bool:
        return self.left.check_sync(wa, update) or self.right.check_sync(wa, update)

    async def check_async(self, wa: WhatsApp, update: _T) -> bool:
        return await self.left.check_async(wa, update) or await self.right.check_async(
            wa, update
        )

    def has_async(self) -> bool:
        return self.left.has_async() or self.right.has_async()


class NotFilter(Filter[_T]):
    def __init__(self, fil: Filter[_T]):
        self.filter = fil

    def check_sync(self, wa: WhatsApp, update: _T) -> bool:
        return not self.filter.check_sync(wa, update)

    async def check_async(self, wa: WhatsApp, update: _T) -> bool:
        return not await self.filter.check_async(wa, update)

    def has_async(self) -> bool:
        return self.filter.has_async()


@overload
def new(
    func: Callable[[WhatsApp, _V], bool | Awaitable[bool]],
    name: str | None = None,
) -> Filter[_V]: ...


@overload
def new(
    func: str | None = None,
    name: str | None = None,
) -> Callable[[Callable[[WhatsApp, _V], bool | Awaitable[bool]]], Filter[_V]]: ...


def new(
    func: Callable[[WhatsApp, Any], bool | Awaitable[bool]] | str | None = None,
    name: str | None = None,
) -> (
    Filter[Any]
    | Callable[[Callable[[WhatsApp, Any], bool | Awaitable[bool]]], Filter[Any]]
):
    """
    A factory function to create custom filter from a function (sync or async).

    >>> from pywa import WhatsApp, filters, types

    >>> wa = WhatsApp(...)

    >>> @filters.new
    ... def is_registered(_: WhatsApp, msg: types.Message) -> bool:
    ...     return my_db.is_user_registered(msg.from_user.bsuid)

    Using it:

    >>> @wa.on_message(is_registered)
    ... def only_registered_users(wa: WhatsApp, msg: types.Message):
    ...     msg.reply("Hello registered user!")

    Or passing the function directly:

    >>> @wa.on_message(filters.new(lambda _, msg: my_db.is_user_registered(msg.from_user.bsuid)))
    ... def only_registered_users(wa: WhatsApp, msg: types.Message):
    ...     msg.reply("Hello registered user!")"""
    if func is None or not callable(func):

        def decorator(
            f: Callable[[WhatsApp, Any], bool | Awaitable[bool]],
        ) -> Filter[Any]:
            return new(f, name=name or (func if isinstance(func, str) else None))

        return decorator
    if not callable(func):
        raise Exception
    is_async = helpers.is_async_callable(func)

    def check_sync(self, wa: WhatsApp, update: Any) -> bool:
        return func(wa, update)

    async def check_async(self, wa: WhatsApp, update: Any) -> bool:
        if is_async:
            return await func(wa, update)
        return func(wa, update)

    def has_async(self) -> bool:
        return is_async

    return type(
        name or getattr(func, "__name__", None) or Filter.__name__
        if hasattr(Filter, "__name__")
        else "Filter",
        (Filter,),
        {
            "check_sync": check_sync,
            "check_async": check_async,
            "has_async": has_async,
        },
    )()


true: Filter[Any] = new(lambda _, __: True, name="true")
"""Filter that always returns True."""

false: Filter[Any] = new(lambda _, __: False, name="false")
"""Filter that always returns False."""


def webhook_fields(*fields: str) -> Filter[types.RawUpdate]:
    """
    Filter for raw updates that contain any of the specified fields.

    >>> filters.webhook_fields("messages")
    """
    _fields = set(fields)
    return new(lambda _, r: r.field in _fields, name="webhook_fields")


forwarded: Filter[types.Message] = new(
    lambda _, m: m.forwarded,
    name="forwarded",
)
"""
Filter for forwarded messages.

>>> filters.forwarded
"""

forwarded_many_times: Filter[types.Message] = new(
    lambda _, m: m.forwarded_many_times, name="forwarded_many_times"
)
"""
Filter for messages that have been forwarded many times.

>>> filters.forwarded_many_times
"""

reply: Filter[types.Message] = new(
    lambda _, m: m.reply_to_message is not None, name="reply"
)
"""
Filter for messages that reply to another message.

>>> filters.reply
"""

without_wa_id: Filter[types.base_update.BaseUserUpdate] = new(
    lambda _, u: u.from_user.wa_id is None, name="without_wa_id"
)
"""
Filter for updates that their sender doesn't have a ``wa_id`` (when the user enables username)
"""


def update_id(id_: str) -> Filter[types.base_update.BaseUpdate]:
    """
    Filter for updates that have the given id.

    >>> update_id("wamid.HBKHUIyNTM4NjAfiefhwojfMTNFQ0Q2MERGRjVDMUHUIGGA=")
    """
    return new(lambda _, u: u.id == id_, name="update_id")


def waba_id(id_: str) -> Filter[types.base_update.BaseUpdate]:
    """
    Filter for updates that their WABA ID matches the given id.

    >>> waba_id("105102735943269")
    """
    return new(lambda _, u: getattr(u, "waba_id", u.id) == id_, name="waba_id")


def replays_to(*msg_ids: str) -> Filter[types.Message]:
    """
    Filter for messages that reply to any of the given message ids.

    >>> replays_to("wamid.HBKHUIyNTM4NjAfiefhwojfMTNFQ0Q2MERGRjVDMUHUIGGA=")
    """
    return new(
        lambda _, m: (
            m.reply_to_message is not None and m.reply_to_message.message_id in msg_ids
        )
    )


has_referred_product = new(
    lambda _, m: (
        m.reply_to_message is not None
        and m.reply_to_message.referred_product is not None
    ),
    name="has_referred_product",
)
"""
Filter for messages that user sends to ask about a product

>>> filters.referred_product
"""

private: Filter[types.Message] = new(
    lambda _, m: m.chat.type == chat.ChatType.PRIVATE, name="private"
)
"""Filter for messages that are sent in private chats."""

group: Filter[types.Message] = new(
    lambda _, m: m.chat.type == chat.ChatType.GROUP, name="group"
)
"""Filter for messages that are sent in group chats."""


def sent_to(
    *, display_phone_number: str = None, phone_number_id: str = None
) -> Filter[base_update.BaseUserUpdate]:
    """
    Filter for updates that are sent to the given phone number.

    - Use this filter when you choose not filter updates (e.g. ``WhatsApp(..., filter_updates=False)``) so you can still filter for messages that are sent to specific phone numbers.


    >>> sent_to(display_phone_number="+1 555-555-5555")
    >>> sent_to(phone_number_id="123456789")
    """
    if not (display_phone_number or phone_number_id):
        raise ValueError(
            "You must provide either display_phone_number or phone_number_id"
        )
    return new(
        lambda _, m: (
            m.metadata.display_phone_number == display_phone_number
            if display_phone_number
            else m.metadata.phone_number_id == phone_number_id
        ),
        name="sent_to",
    )


sent_to_me: Filter[base_update.BaseUserUpdate] = new(
    lambda wa, m: sent_to(phone_number_id=wa.phone_id).check_sync(wa, m),
    name="sent_to_me",
)
"""
Filter for updates that are sent to the client phone number.

- Use this filter when you choose not filter updates (e.g. ``WhatsApp(..., filter_updates=False)``) so you can still filter for messages that are sent to the client phone number.

>>> sent_to_me
"""


def from_users(
    *ids: str,
) -> Filter[base_update.BaseUserUpdate]:
    """
    Filter for updates that are sent from the given IDs (BSUID, PARENT_BSUID, WA_ID, or PHONE_NUMBER).

    >>> from_users("US.13491208655302741918", "+1 (631) 555-1234", "16315551234")
    """
    from .types.sent_update import RecipientType

    only_nums_pattern = re.compile(r"\D")
    processed_ids = set()

    for identifier in ids:
        id_type = RecipientType.from_recipient(identifier)
        if id_type == RecipientType.GROUP_ID:
            continue
        if id_type == RecipientType.PHONE_NUMBER:
            clean_id = re.sub(only_nums_pattern, "", identifier)
            processed_ids.add(clean_id)
        else:
            processed_ids.add(identifier)

    def filter_func(_, m) -> bool:
        user = m.from_user

        return (
            user.bsuid in processed_ids
            or user.wa_id in processed_ids
            or user.parent_bsuid in processed_ids
            or user.username in processed_ids
        )

    return new(filter_func, name="from_users")


def from_countries(
    *prefixes_or_codes: str | int,
) -> Filter[base_update.BaseUserUpdate]:
    """
    Filter for updates that are sent from the given country codes.

    - You can pass either country codes (e.g. "US", "IL") or phone number prefixes (e.g. "+1", "972").
    - See https://countrycode.org/ for a list of country codes.

    >>> from_countries("972", "1", "+972", "US", "IL") # Israel and USA
    """
    codes = tuple(str(p) for p in prefixes_or_codes)
    country_codes = {c.upper() for c in codes if c.isalpha()}
    phone_prefixes = tuple((c.lstrip("+")) for c in codes if not c.isalpha())
    return new(
        lambda _, m: (
            m.from_user.country_code in country_codes  # country_code always exists
            or (m.from_user.wa_id and m.from_user.wa_id.startswith(phone_prefixes))
        ),
        name="from_countries",
    )


def from_groups(*group_ids: str) -> Filter[base_update.BaseUserUpdate]:
    """
    Filter for updates that are sent from the given group ids.

    >>> from_groups("Y2FwaV9ncm91cDoxNzA1NTU1MDEzOToxMjAzNjM0MDQ2OTQyMzM4MjAZD")
    """
    return new(lambda _, m: m.chat.id in group_ids, name="from_groups")


def matches(*strings: str, ignore_case: bool = False) -> Filter[Any]:
    """
    Filter for messages that are matching (``==``) any of the given strings.

    The strings will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``
        - :class:`FlowCompletion`: ``token``, ``body``

    >>> matches("Hello", "Hi")

    Args:
        *strings: The strings to match.
        ignore_case: Whether to ignore case when matching.
    """
    strings = tuple(m.lower() for m in strings) if ignore_case else strings
    return new(
        lambda _, m: (
            any(
                (txt.lower() if ignore_case else txt) in strings
                for txt_field in m._txt_fields
                if (txt := getattr(m, txt_field)) is not None
            )
            if getattr(m, "_txt_fields", None)
            else False
        ),
        name="matches",
    )


def startswith(*prefixes: str, ignore_case: bool = False) -> Filter[Any]:
    """
    Filter for updates that start with any of the given prefixes.

    The prefixes will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``
        - :class:`FlowCompletion`: ``token``, ``body``

    >>> startswith("Hello", "Hi", ignore_case=True)

    Args:
        *prefixes: The prefixes to match.
        ignore_case: Whether to ignore case when matching.
    """
    prefixes = tuple(m.lower() for m in prefixes) if ignore_case else prefixes
    return new(
        lambda _, u: (
            any(
                (txt.lower() if ignore_case else txt).startswith(prefixes)
                for txt_field in u._txt_fields
                if (txt := getattr(u, txt_field)) is not None
            )
            if getattr(u, "_txt_fields", None)
            else False
        ),
        name="startswith",
    )


def endswith(*suffixes: str, ignore_case: bool = False) -> Filter[Any]:
    """
    Filter for updates that end with any of the given suffixes.

    The suffixes will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``
        - :class:`FlowCompletion`: ``token``, ``body``

    >>> endswith("Hello", "Hi", ignore_case=True)

    Args:
        *suffixes: The suffixes to match.
        ignore_case: Whether to ignore case when matching.
    """
    suffixes = tuple(m.lower() for m in suffixes) if ignore_case else suffixes
    return new(
        lambda _, u: (
            any(
                (txt.lower() if ignore_case else txt).endswith(suffixes)
                for txt_field in u._txt_fields
                if (txt := getattr(u, txt_field)) is not None
            )
            if getattr(u, "_txt_fields", None)
            else False
        ),
        name="endswith",
    )


def contains(*words: str, ignore_case: bool = False) -> Filter[Any]:
    """
    Filter for updates that contain any of the given words.

    The words will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``
        - :class:`FlowCompletion`: ``token``, ``body``

    >>> contains("Hello", "Hi", ignore_case=True)

    Args:
        *words: The words to match.
        ignore_case: Whether to ignore case when matching.
    """
    words = tuple(m.lower() for m in words) if ignore_case else words
    return new(
        lambda _, u: (
            any(
                word in (txt.lower() if ignore_case else txt)
                for word in words
                for txt_field in u._txt_fields
                if (txt := getattr(u, txt_field)) is not None
            )
            if getattr(u, "_txt_fields", None)
            else False
        ),
        name="contains",
    )


def regex(*patterns: str | re.Pattern, flags: int = 0) -> Filter[Any]:
    """
    Filter for updates that match any of the given regex patterns.

    The patterns will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``
        - :class:`FlowCompletion`: ``token``, ``body``

    >>> regex(r"Hello|Hi")

    Args:
        *patterns: The regex patterns to match.
        flags: The regex flags to use.
    """
    patterns = tuple(
        p if isinstance(p, re.Pattern) else re.compile(p, flags) for p in patterns
    )
    return new(
        lambda _, u: (
            any(
                re.match(p, txt)
                for p in patterns
                for txt_field in u._txt_fields
                if (txt := getattr(u, txt_field)) is not None
            )
            if getattr(u, "_txt_fields", None)
            else False
        ),
        name="regex",
    )


message: Filter[types.Message] = new(
    lambda _, m: isinstance(m, types.Message), name="message"
)
"""Filter for all messages."""


def mimetypes(*mmtps: str) -> Filter[types.Message]:
    """
    Filter for media messages that match any of the given mime types.

    - `Supported Media Types on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types>`_.

    >>> mimetypes("application/pdf", "image/png")
    """
    return new(
        lambda _, m: m.media.mime_type in mmtps,
        name="mimetypes",
    )


def extensions(*exts: str) -> Filter[types.Message]:
    """
    Filter for media messages that match any of the given extensions.

    >>> extensions(".pdf", ".png")
    """
    return new(
        lambda _, m: m.media.extension in exts,
        name="extensions",
    )


media: Filter[types.Message] = new(lambda _, m: m.has_media, name="media")
"""Filter for media messages (images, videos, documents, audio, stickers)."""

is_command: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.TEXT and m.text.startswith(("/", "!")),
    name="is_command",
)
"""
Filter for text messages that are commands (start with ``/`` or ``!``).

>>> filters.is_command
"""


def command(
    *cmds: str,
    prefixes: str | Iterable[str] = "/!",
    ignore_case: bool = False,
) -> Filter[types.Message]:
    """
    Filter for text messages that are commands.


    >>> command("start", "hello", prefixes="/", ignore_case=True)

    Args:
        *cmds: The command/s to filter for (e.g. "start", "hello").
        prefixes: The prefix/s to filter for (default: "/!", i.e. "/start").
        ignore_case: Whether to ignore case when matching (default: ``False``).
    """
    cmds = tuple(c.lower() for c in cmds) if ignore_case else cmds
    return new(
        lambda _, m: (
            m.type == types.MessageType.TEXT
            and (
                m.text[0] in prefixes
                and (m.text[1:].lower() if ignore_case else m.text[1:]).startswith(cmds)
            )
        ),
        name="command",
    )


text: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.TEXT, name="text"
)
"""Filter for text messages."""

has_caption: Filter[types.Message] = new(
    lambda _, m: m.caption is not None,
    name="media_has_caption",
)
"""Filter for media messages that have a caption."""

image: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.IMAGE, name="image"
)
"""Filter for image messages."""

video: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.VIDEO, name="video"
)
"""Filter for video messages."""

document: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.DOCUMENT, name="document"
)
"""Filter for document messages."""

audio: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.AUDIO, name="audio"
)
"""Filter for audio messages (both voice notes and audio files)."""

audio_only: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.AUDIO and not m.audio.voice,
    name="audio_only",
)
"""Filter for audio messages that are not voice notes."""

voice: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.AUDIO and m.audio.voice, name="voice"
)
"""Filter for audio messages that are voice notes."""

sticker: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.STICKER, name="sticker"
)
"""Filter for sticker messages (both static and animated)."""

animated_sticker: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.STICKER and m.sticker.animated,
    name="animated_sticker",
)
"""Filter for animated sticker messages."""

static_sticker: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.STICKER and not m.sticker.animated,
    name="static_sticker",
)
"""Filter for static sticker messages."""

location: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.LOCATION, name="location"
)
"""Filter for location messages."""

current_location: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.LOCATION and m.location.current_location,
    name="current_location",
)
"""Filter for location messages that are current locations."""


def location_in_radius(
    lat: float, lon: float, radius: float | int
) -> Filter[types.Message]:
    """
    Filter for location messages that are in a given radius.

    >>> location_in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

    Args:
        lat: Latitude of the center of the radius.
        lon: Longitude of the center of the radius.
        radius: Radius in kilometers.
    """

    return new(
        lambda _, m: (
            m.type == types.MessageType.LOCATION
            and m.location.in_radius(lat=lat, lon=lon, radius=radius)
        ),
        name="location_in_radius",
    )


reaction: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.REACTION, name="reaction"
)
"""Filter for reaction messages (both added and removed)."""

reaction_added: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.REACTION and m.reaction.emoji is not None,
    name="reaction_added",
)
"""Filter for reaction messages that were added to a message."""

reaction_removed: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.REACTION and m.reaction.emoji is None,
    name="reaction_removed",
)
"""Filter for reaction messages that were removed from a message."""


def reaction_emojis(*emojis: str) -> Filter[types.Message]:
    """
    Filter for custom reaction messages. pass emojis as strings.

    >>> reaction_emojis("👍","👎")
    """
    return new(
        lambda _, m: (
            m.type == types.MessageType.REACTION and m.reaction.emoji in emojis
        ),
        name="reaction_emojis",
    )


contacts: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.CONTACTS, name="contacts"
)
"""Filter for contacts messages."""

contact_info_shared: Filter[types.Message] = new(
    lambda _, m: (
        m.type == types.MessageType.CONTACTS
        and m.contacts.origin == ContactsOrigin.CONTACT_REQUEST
    ),
    name="contact_info_shared",
)
"""Filter for contact info shared messages."""

contacts_has_wa: Filter[types.Message] = new(
    lambda _, m: (
        m.type == types.MessageType.CONTACTS
        and (
            any(
                (
                    p.wa_id
                    for p in (
                        phone for contact in m.contacts for phone in contact.phones
                    )
                )
            )
        )
    ),
    name="contacts_any_has_wa",
)
"""Filter for contacts messages that have a WhatsApp account."""

order: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.ORDER, name="order"
)
"""Filter for order messages."""

unsupported: Filter[types.Message] = new(
    lambda _, m: m.type == types.MessageType.UNSUPPORTED, name="unsupported"
)
"""Filter for all unsupported messages."""

callback_button: Filter[types.CallbackButton] = new(
    lambda _, c: isinstance(c, types.CallbackButton), name="callback_button"
)
"""Filter for callback buttons."""

callback_selection: Filter[types.CallbackSelection] = new(
    lambda _, c: isinstance(c, types.CallbackSelection), name="callback_selection"
)
"""Filter for callback selections."""

message_status: Filter[types.MessageStatus] = new(
    lambda _, s: isinstance(s, types.MessageStatus), name="message_status"
)

sent: Filter[types.MessageStatus] = new(
    lambda _, s: s.status == types.MessageStatusType.SENT, name="status_sent"
)
"""Filter for messages that have been sent."""

delivered: Filter[types.MessageStatus] = new(
    lambda _, s: s.status == types.MessageStatusType.DELIVERED, name="status_delivered"
)
"""Filter for messages that have been delivered."""

read: Filter[types.MessageStatus] = new(
    lambda _, s: s.status == types.MessageStatusType.READ, name="status_read"
)
"""Filter for messages that have been read."""

failed: Filter[types.MessageStatus] = new(
    lambda _, s: s.status == types.MessageStatusType.FAILED, name="status_failed"
)
"""Filter for status updates of messages that have failed to send."""

played: Filter[types.MessageStatus] = new(
    lambda _, s: s.status == types.MessageStatusType.PLAYED, name="status_played"
)
"""Filter for status updates of voice messages that have been played."""


def failed_with(
    *errors: type[WhatsAppError] | int,
) -> Filter[types.MessageStatus]:
    """
    Filter for status updates of messages that have failed to send with the given error/s.

    Args:
        *errors: The exceptions from :mod:`pywa.errors` or error codes to match.

    >>> failed_with(ReEngagementMessage)
    >>> failed_with(131051)
    """
    error_codes = tuple(c for c in errors if isinstance(c, int))
    exceptions = tuple(
        e for e in errors if e not in error_codes and issubclass(e, WhatsAppError)
    )
    return new(
        lambda _, s: (
            s.status == types.MessageStatusType.FAILED
            and (
                any((isinstance(s.error, e) for e in exceptions))
                or s.error.code in error_codes
            )
        ),
        name="status_failed_with",
    )


with_tracker: Filter[types.MessageStatus] = new(
    lambda _, s: s.tracker is not None, name="with_tracker"
)
"""Filter for status updates that have a tracker."""

template_status: Filter[types.TemplateStatusUpdate] = new(
    lambda _, s: isinstance(s, types.TemplateStatusUpdate), name="template_status"
)
"""Filters for template status updates."""

template_status_approved: Filter[types.TemplateStatusUpdate] = new(
    lambda _, s: s.new_status == types.templates.TemplateStatus.APPROVED,
    name="template_status_approved",
)

template_status_rejected: Filter[types.TemplateStatusUpdate] = new(
    lambda _, s: s.new_status == types.templates.TemplateStatus.REJECTED,
    name="template_status_rejected",
)

template_quality: Filter[types.TemplateQualityUpdate] = new(
    lambda _, s: isinstance(s, types.TemplateQualityUpdate), name="template_quality"
)
"""Filters for template quality updates."""

template_category: Filter[types.TemplateCategoryUpdate] = new(
    lambda _, s: isinstance(s, types.TemplateCategoryUpdate), name="template_category"
)
"""Filters for template category updates."""

template_components: Filter[types.TemplateComponentsUpdate] = new(
    lambda _, s: isinstance(s, types.TemplateComponentsUpdate),
    name="template_components",
)
"""Filters for template components updates."""

flow_completion: Filter[types.FlowCompletion] = new(
    lambda _, f: isinstance(f, types.FlowCompletion), name="flow_completion"
)
"""Filter for flow completion updates."""

call_connect: Filter[types.CallConnect] = new(
    lambda _, c: isinstance(c, types.CallConnect), name="call_connect"
)
"""Filter for call connect updates."""

outgoing_call: Filter[types.CallConnect] = new(
    lambda _, c: c.direction == types.calls.CallDirection.BUSINESS_INITIATED,
    name="outgoing_call",
)
incoming_call: Filter[types.CallConnect] = new(
    lambda _, c: c.direction == types.calls.CallDirection.USER_INITIATED,
    name="incoming_call",
)
"""Filter for incoming call updates."""

call_status: Filter[types.CallStatus] = new(
    lambda _, c: isinstance(c, types.CallStatus), name="call_status"
)
"""Filter for call status updates."""

call_answered: Filter[types.CallStatus] = new(
    lambda _, c: c.status == types.calls.CallStatusType.ACCEPTED,
    name="call_answered",
)
call_rejected: Filter[types.CallStatus] = new(
    lambda _, c: c.status == types.calls.CallStatusType.REJECTED, name="call_rejected"
)
call_ringing: Filter[types.CallStatus] = new(
    lambda _, c: c.status == types.calls.CallStatusType.RINGING, name="call_ringing"
)

call_permission_update: Filter[types.CallPermissionUpdate] = new(
    lambda _, c: isinstance(c, types.CallPermissionUpdate),
    name="call_permission_update",
)
"""Filter for call permission updates."""

call_permission_accepted: Filter[types.CallPermissionUpdate] = new(
    lambda _, c: c.response == types.calls.CallPermissionResponse.ACCEPT,
    name="call_permission_accepted",
)
call_permission_rejected: Filter[types.CallPermissionUpdate] = new(
    lambda _, c: c.response == types.calls.CallPermissionResponse.REJECT,
    name="call_permission_rejected",
)

call_terminate: Filter[types.CallTerminate] = new(
    lambda _, c: isinstance(c, types.CallTerminate), name="call_terminate"
)
"""Filter for call terminate updates."""

phone_number_change: Filter[types.PhoneNumberChange] = new(
    lambda _, c: isinstance(c, types.PhoneNumberChange), name="phone_number_change"
)
"""Filter for phone number change updates."""

identity_change: Filter[types.IdentityChange] = new(
    lambda _, c: isinstance(c, types.IdentityChange), name="identity_change"
)
"""Filter for identity change updates."""

user_marketing_preferences: Filter[types.UserMarketingPreferences] = new(
    lambda _, m: isinstance(m, types.UserMarketingPreferences),
    name="user_marketing_preferences",
)
"""Filter for user marketing preferences updates."""

user_marketing_preferences_stop: Filter[types.UserMarketingPreferences] = new(
    lambda _, m: not bool(m),
    name="user_marketing_preferences_stop",
)
"""Filter for user marketing preferences updates that indicate the user has requested to stop receiving marketing messages."""
user_marketing_preferences_resume: Filter[types.UserMarketingPreferences] = new(
    lambda _, m: bool(m),
    name="user_marketing_preferences_resume",
)
"""Filter for user marketing preferences updates that indicate the user has requested to resume receiving marketing messages."""

account_update: Filter[types.AccountUpdate] = new(
    lambda _, u: isinstance(u, types.AccountUpdate), name="account_update"
)
"""Filter for account update updates."""

account_deleted: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.ACCOUNT_DELETED,
    name="account_deleted",
)
account_restriction: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.ACCOUNT_RESTRICTION,
    name="account_restriction",
)
account_violation: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.ACCOUNT_VIOLATION,
    name="account_violation",
)
ad_account_linked: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.AD_ACCOUNT_LINKED,
    name="ad_account_linked",
)
auth_intl_price_eligibility_update: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event
        == types.account_update.AccountUpdateEvent.AUTH_INTL_PRICE_ELIGIBILITY_UPDATE
    ),
    name="auth_intl_price_eligibility_update",
)
business_primary_location_country_update: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event
        == types.account_update.AccountUpdateEvent.BUSINESS_PRIMARY_LOCATION_COUNTRY_UPDATE
    ),
    name="business_primary_location_country_update",
)
account_disabled: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.DISABLED_UPDATE,
    name="account_disabled",
)
mm_lite_terms_signed: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event == types.account_update.AccountUpdateEvent.MM_LITE_TERMS_SIGNED
    ),
    name="mm_lite_terms_signed",
)
partner_added: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.PARTNER_ADDED,
    name="partner_added",
)
partner_app_installed: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event == types.account_update.AccountUpdateEvent.PARTNER_APP_INSTALLED
    ),
    name="partner_app_installed",
)
partner_app_uninstalled: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event == types.account_update.AccountUpdateEvent.PARTNER_APP_UNINSTALLED
    ),
    name="partner_app_uninstalled",
)
partner_client_certification_status_update: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event
        == types.account_update.AccountUpdateEvent.PARTNER_CLIENT_CERTIFICATION_STATUS_UPDATE
    ),
    name="partner_client_certification_status_update",
)
partner_removed: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.PARTNER_REMOVED,
    name="partner_removed",
)
volume_based_pricing_tier_update: Filter[types.AccountUpdate] = new(
    lambda _, u: (
        u.event
        == types.account_update.AccountUpdateEvent.VOLUME_BASED_PRICING_TIER_UPDATE
    ),
    name="volume_based_pricing_tier_update",
)
account_offboarded: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.ACCOUNT_OFFBOARDED,
    name="account_offboarded",
)
account_reconnected: Filter[types.AccountUpdate] = new(
    lambda _, u: u.event == types.account_update.AccountUpdateEvent.ACCOUNT_RECONNECTED,
    name="account_reconnected",
)
