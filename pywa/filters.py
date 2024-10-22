"""
Usefully filters to use in your handlers.

>>> from pywa import filters as fil
>>> from pywa import WhatsApp, types
>>> wa = WhatsApp(...)

>>> @wa.on_message(fil.text.command("start"))
... def on_hi_msg(_: WhatsApp, m: types.Message):
...     print("This is a welcome message!")
"""

from __future__ import annotations

__all__ = [
    "new",
    "update_id",
    "forwarded",
    "forwarded_many_times",
    "reply",
    "replays_to",
    "has_referred_product",
    "sent_to",
    "sent_to_me",
    "from_users",
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
    "contacts_has_wa",
    "order",
    "callback_button",
    "callback_selection",
    "message_status",
    "sent",
    "delivered",
    "read",
    "failed",
    "failed_with",
    "with_tracker",
    "flow_completion",
    "template_status",
    "chat_opened",
]

import re
from typing import TYPE_CHECKING, Callable, Iterable, TypeVar, Awaitable, Any

from .errors import ReEngagementMessage, WhatsAppError
from . import utils
from .types import Message as _Msg
from .types import CallbackButton as _Clb
from .types import CallbackSelection as _Cls
from .types import MessageStatus as _Ms
from .types import MessageStatusType as _Mst
from .types import MessageType as _Mt
from .types import TemplateStatus as _Ts
from .types import FlowCompletion as _Fc
from .types import ChatOpened as _Co
from .types.base_update import (
    BaseUpdate as _BaseUpdate,
)  # noqa

if TYPE_CHECKING:
    from pywa import WhatsApp as _Wa


_T = TypeVar("_T", bound=_BaseUpdate)


class Filter:
    """Base filter class handling both sync and async."""

    def check_sync(self, wa: _Wa, update: Any) -> bool:
        raise NotImplementedError

    async def check_async(self, wa: _Wa, update: Any) -> bool:
        raise NotImplementedError

    def has_async(self) -> bool:
        raise NotImplementedError

    def __and__(self, other: Filter) -> Filter:
        return AndFilter(self, other)

    def __or__(self, other: Filter) -> Filter:
        return OrFilter(self, other)

    def __invert__(self) -> Filter:
        return NotFilter(self)


class AndFilter(Filter):
    def __init__(self, left: Filter, right: Filter):
        self.left = left
        self.right = right

    def check_sync(self, wa: _Wa, update: _T) -> bool:
        return self.left.check_sync(wa, update) and self.right.check_sync(wa, update)

    async def check_async(self, wa: _Wa, update: _T) -> bool:
        return await self.left.check_async(wa, update) and await self.right.check_async(
            wa, update
        )

    def has_async(self) -> bool:
        return self.left.has_async() or self.right.has_async()


class OrFilter(Filter):
    def __init__(self, left: Filter, right: Filter):
        self.left = left
        self.right = right

    def check_sync(self, wa: _Wa, update: _T) -> bool:
        return self.left.check_sync(wa, update) or self.right.check_sync(wa, update)

    async def check_async(self, wa: _Wa, update: _T) -> bool:
        return await self.left.check_async(wa, update) or await self.right.check_async(
            wa, update
        )

    def has_async(self) -> bool:
        return self.left.has_async() or self.right.has_async()


class NotFilter(Filter):
    def __init__(self, fil: Filter):
        self.filter = fil

    def check_sync(self, wa: _Wa, update: _T) -> bool:
        return not self.filter.check_sync(wa, update)

    async def check_async(self, wa: _Wa, update: _T) -> bool:
        return not await self.filter.check_async(wa, update)

    def has_async(self) -> bool:
        return self.filter.has_async()


def new(
    func: Callable[[_Wa, _T], bool | Awaitable[bool]], name: str | None = None
) -> Filter:
    """Factory function to create a filter from a function (sync or async)."""

    is_async = utils.is_async_callable(func)

    def check_sync(self, wa: _Wa, update: _T) -> bool:
        return func(wa, update)

    async def check_async(self, wa: _Wa, update: _T) -> bool:
        if is_async:
            return await func(wa, update)
        return func(wa, update)

    def has_async(self) -> bool:
        return is_async

    return type(
        name or func.__name__ or Filter,
        (Filter,),
        {
            "check_sync": check_sync,
            "check_async": check_async,
            "has_async": has_async,
        },
    )()


forwarded = new(
    lambda _, m: m.forwarded,
    name="forwarded",
)
"""
Filter for forwarded messages.

>>> filters.forwarded
"""

forwarded_many_times = new(
    lambda _, m: m.forwarded_many_times, name="forwarded_many_times"
)
"""
Filter for messages that have been forwarded many times.

>>> filters.forwarded_many_times
"""

reply = new(lambda _, m: m.reply_to_message is not None, name="reply")
"""
Filter for messages that reply to another message.

>>> filters.reply
"""


def update_id(id_: str) -> Filter:
    """
    Filter for updates that have the given id.

    >>> update_id("wamid.HBKHUIyNTM4NjAfiefhwojfMTNFQ0Q2MERGRjVDMUHUIGGA=")
    """
    return new(lambda _, u: u.id == id_, name="update_id")


def replays_to(*msg_ids: str) -> Filter:
    """
    Filter for messages that reply to any of the given message ids.

    >>> replays_to("wamid.HBKHUIyNTM4NjAfiefhwojfMTNFQ0Q2MERGRjVDMUHUIGGA=")
    """
    return new(
        lambda _, m: m.reply_to_message is not None
        and m.reply_to_message.message_id in msg_ids
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


def sent_to(*, display_phone_number: str = None, phone_number_id: str = None) -> Filter:
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


sent_to_me = new(
    lambda wa, m: sent_to(phone_number_id=wa.phone_id).check_sync(wa, m),
    name="sent_to_me",
)
"""
Filter for updates that are sent to the client phone number.

- Use this filter when you choose not filter updates (e.g. ``WhatsApp(..., filter_updates=False)``) so you can still filter for messages that are sent to the client phone number.

>>> sent_to_me
"""


def from_users(
    *numbers: str,
) -> Filter:
    """
    Filter for updates that are sent from the given numbers.

    >>> from_users("+1 555-555-5555", "972123456789")
    """
    only_nums_pattern = re.compile(r"\D")
    numbers = tuple(re.sub(only_nums_pattern, "", n) for n in numbers)
    return new(lambda _, m: m.from_user.wa_id in numbers, name="from_users")


def from_countries(
    *prefixes: str | int,
) -> Filter:
    """
    Filter for updates that are sent from the given country codes.

    - See https://countrycode.org/ for a list of country codes.

    It is always recommended to restrict the countries that can use your bot. remember that you pay for
    every conversation that you reply to.

    >>> from_countries("972", "1") # Israel and USA
    """
    codes = tuple(str(p) for p in prefixes)
    return new(lambda _, m: m.from_user.wa_id.startswith(codes), name="from_countries")


def matches(*strings: str, ignore_case: bool = False) -> Filter:
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
        lambda _, m: any(
            (txt.lower() if ignore_case else txt) in strings
            for txt_field in m._txt_fields
            if (txt := getattr(m, txt_field)) is not None
        )
        if getattr(m, "_txt_fields", None)
        else False,
        name="matches",
    )


def startswith(*prefixes: str, ignore_case: bool = False) -> Filter:
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
        lambda _, u: any(
            (txt.lower() if ignore_case else txt).startswith(prefixes)
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False,
        name="startswith",
    )


def endswith(*suffixes: str, ignore_case: bool = False) -> Filter:
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
        lambda _, u: any(
            (txt.lower() if ignore_case else txt).endswith(suffixes)
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False,
        name="endswith",
    )


def contains(*words: str, ignore_case: bool = False) -> Filter:
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
        lambda _, u: any(
            word in (txt.lower() if ignore_case else txt)
            for word in words
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False,
        name="contains",
    )


def regex(*patterns: str | re.Pattern, flags: int = 0) -> Filter:
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
        lambda _, u: any(
            re.match(p, txt)
            for p in patterns
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False,
        name="regex",
    )


message = new(lambda _, m: isinstance(m, _Msg), name="message")
"""Filter for all messages."""


def mimetypes(*mmtps: str) -> Filter:
    """
    Filter for media messages that match any of the given mime types.

    - `Supported Media Types on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types>`_.

    >>> mimetypes("application/pdf", "image/png")
    """
    return new(
        lambda _, m: m.media.mime_type in mmtps,
        name="mimetypes",
    )


def extensions(*exts: str) -> Filter:
    """
    Filter for media messages that match any of the given extensions.

    >>> extensions(".pdf", ".png")
    """
    return new(
        lambda _, m: m.media.extension in exts,
        name="extensions",
    )


media = new(lambda _, m: m.has_media, name="media")
"""Filter for media messages (images, videos, documents, audio, stickers)."""

is_command = new(
    lambda _, m: m.type == _Mt.TEXT and m.text.startswith(("/", "!")),
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
) -> Filter:
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
        lambda _, m: m.type == _Mt.TEXT
        and (
            m.text[0] in prefixes
            and (m.text[1:].lower() if ignore_case else m.text[1:]).startswith(cmds)
        ),
        name="command",
    )


text = new(lambda _, m: m.type == _Mt.TEXT, name="text")
"""Filter for text messages."""

has_caption = new(
    lambda _, m: m.caption is not None,
    name="media_has_caption",
)
"""Filter for media messages that have a caption."""

image = new(lambda _, m: m.type == _Mt.IMAGE, name="image")
"""Filter for image messages."""

video = new(lambda _, m: m.type == _Mt.VIDEO, name="video")
"""Filter for video messages."""

document = new(lambda _, m: m.type == _Mt.DOCUMENT, name="document")
"""Filter for document messages."""

audio = new(lambda _, m: m.type == _Mt.AUDIO, name="audio")
"""Filter for audio messages (both voice notes and audio files)."""

audio_only = new(
    lambda _, m: m.type == _Mt.AUDIO and not m.audio.voice, name="audio_only"
)
"""Filter for audio messages that are not voice notes."""

voice = new(lambda _, m: m.type == _Mt.AUDIO and m.audio.voice, name="voice")
"""Filter for audio messages that are voice notes."""

sticker = new(lambda _, m: m.type == _Mt.STICKER, name="sticker")
"""Filter for sticker messages (both static and animated)."""

animated_sticker = new(
    lambda _, m: m.type == _Mt.STICKER and m.sticker.animated, name="animated_sticker"
)
"""Filter for animated sticker messages."""

static_sticker = new(
    lambda _, m: m.type == _Mt.STICKER and not m.sticker.animated, name="static_sticker"
)
"""Filter for static sticker messages."""

location = new(lambda _, m: m.type == _Mt.LOCATION, name="location")
"""Filter for location messages."""

current_location = new(
    lambda _, m: m.type == _Mt.LOCATION and m.location.current_location,
    name="current_location",
)
"""Filter for location messages that are current locations."""


def location_in_radius(lat: float, lon: float, radius: float | int) -> Filter:
    """
    Filter for location messages that are in a given radius.

    >>> location_in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

    Args:
        lat: Latitude of the center of the radius.
        lon: Longitude of the center of the radius.
        radius: Radius in kilometers.
    """

    return new(
        lambda _, m: m.type == _Mt.LOCATION
        and m.location.in_radius(lat=lat, lon=lon, radius=radius),
        name="location_in_radius",
    )


reaction = new(lambda _, m: m.type == _Mt.REACTION, name="reaction")
"""Filter for reaction messages (both added and removed)."""


reaction_added = new(
    lambda _, m: m.type == _Mt.REACTION and m.reaction.emoji is not None,
    name="reaction_added",
)
"""Filter for reaction messages that were added to a message."""


reaction_removed = new(
    lambda _, m: m.type == _Mt.REACTION and m.reaction.emoji is None,
    name="reaction_removed",
)
"""Filter for reaction messages that were removed from a message."""


def reaction_emojis(*emojis: str) -> Filter:
    """
    Filter for custom reaction messages. pass emojis as strings.

    >>> reaction_emojis("👍","👎")
    """
    return new(
        lambda _, m: m.type == _Mt.REACTION and m.reaction.emoji in emojis,
        name="reaction_emojis",
    )


contacts = new(lambda _, m: m.type == _Mt.CONTACTS, name="contacts")
"""Filter for contacts messages."""


contacts_has_wa = new(
    lambda _, m: m.type == _Mt.CONTACTS
    and (
        any(
            (
                p.wa_id
                for p in (phone for contact in m.contacts for phone in contact.phones)
            )
        )
    ),
    name="contacts_any_has_wa",
)
"""Filter for contacts messages that have a WhatsApp account."""


order = new(lambda _, m: m.type == _Mt.ORDER, name="order")
"""Filter for order messages."""


unsupported = new(lambda _, m: m.type == _Mt.UNSUPPORTED, name="unsupported")
"""Filter for all unsupported messages."""


callback_button = new(lambda _, c: isinstance(c, _Clb), name="callback_button")
"""Filter for callback buttons."""

callback_selection = new(lambda _, c: isinstance(c, _Cls), name="callback_selection")
"""Filter for callback selections."""

message_status = new(lambda _, s: isinstance(s, _Ms), name="message_status")

sent = new(lambda _, s: s.status == _Mst.SENT, name="status_sent")
"""Filter for messages that have been sent."""

delivered = new(lambda _, s: s.status == _Mst.DELIVERED, name="status_delivered")
"""Filter for messages that have been delivered."""

read = new(lambda _, s: s.status == _Mst.READ, name="status_read")
"""Filter for messages that have been read."""

failed = new(lambda _, s: s.status == _Mst.FAILED, name="status_failed")
"""Filter for status updates of messages that have failed to send."""


def failed_with(
    *errors: type[WhatsAppError] | int,
) -> Filter:
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
        lambda _, s: s.status == _Mst.FAILED
        and (
            any((isinstance(s.error, e) for e in exceptions))
            or s.error.error_code in error_codes
        ),
        name="status_failed_with",
    )


with_tracker = new(lambda _, s: s.tracker is not None, name="with_tracker")
"""Filter for status updates that have a tracker."""

template_status = new(lambda _, s: isinstance(s, _Ts), name="template_status")
"""Filters for template status updates."""

flow_completion = new(lambda _, f: isinstance(f, _Fc), name="flow_completion")
"""Filter for flow completion updates."""

chat_opened = new(lambda _, c: isinstance(c, _Co), name="chat_opened")
"""Filter for chat opened updates."""
