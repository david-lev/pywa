"""
Usefully filters to use in your handlers.

>>> from pywa import filters as fil
>>> from pywa import WhatsApp, types
>>> wa = WhatsApp(...)

>>> @wa.on_message(fil.startswith("Hi", "Hello", ignore_case=True))
... def on_hi_msg(_: WhatsApp, m: types.Message):
...     print("This is a welcome message!")
"""

from __future__ import annotations

__all__ = [
    "all_",
    "any_",
    "not_",
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
    "text",
    "media",
    "image",
    "video",
    "audio",
    "document",
    "sticker",
    "reaction",
    "unsupported",
    "location",
    "contacts",
    "order",
    "callback",
    "message_status",
    "template_status",
]

import abc
import re
from typing import TYPE_CHECKING, Callable, Iterable, TypeAlias, TypeVar
from pywa import utils as _utils
from .errors import ReEngagementMessage, WhatsAppError
from .types import CallbackButton as _Clb, CallbackSelection as _Cls
from .types import Message as _Msg
from .types import MessageStatus as _Ms
from .types import MessageStatusType as _Mst
from .types import MessageType as _Mt
from .types import TemplateStatus as _Ts
from .types.base_update import BaseUpdate as _BaseUpdate  # noqa

if TYPE_CHECKING:
    from pywa import WhatsApp as _Wa

    _MessageFilterT: TypeAlias = Callable[[_Wa, _Msg], bool]
    _CallbackFilterT: TypeAlias = Callable[[_Wa, _Clb | _Cls], bool]
    _MessageStatusFilterT: TypeAlias = Callable[[_Wa, _Ms], bool]
    _TemplateStatusFilterT: TypeAlias = Callable[[_Wa, _Ts], bool]

_T = TypeVar("_T", bound=_BaseUpdate)

forwarded: _MessageFilterT = lambda _, m: m.forwarded  # Filter for forwarded messages.
"""
Filter for forwarded messages.

>>> filters.forwarded
"""

forwarded_many_times: _MessageFilterT = lambda _, m: m.forwarded_many_times
"""
Filter for messages that have been forwarded many times.

>>> filters.forwarded_many_times
"""

reply: _MessageFilterT = lambda _, m: m.reply_to_message is not None
"""
Filter for messages that reply to another message.

>>> filters.reply
"""


def replays_to(*msg_ids: str) -> _MessageFilterT:
    """
    Filter for messages that reply to any of the given message ids.

    >>> replays_to("wamid.HBKHUIyNTM4NjAfiefhwojfMTNFQ0Q2MERGRjVDMUHUIGGA=")
    """
    return (
        lambda _, m: m.reply_to_message is not None
        and m.reply_to_message.message_id in msg_ids
    )


has_referred_product: _MessageFilterT = lambda _, m: (
    m.reply_to_message is not None and m.reply_to_message.referred_product is not None
)
"""
Filter for messages that user sends to ask about a product

>>> filters.referred_product
"""


def all_(*filters: Callable[[_Wa, _T], bool]) -> Callable[[_Wa, _T], bool]:
    """
    Returns ``True`` if all the given filters return ``True``. Behaves like ``and`` between filters.

    >>> all_(startswith("Hello"), endswith("Word"))
    """
    return lambda wa, m: all(f(wa, m) for f in filters)


def any_(*filters: Callable[[_Wa, _T], bool]) -> Callable[[_Wa, _T], bool]:
    """
    Returns ``True`` if any of the given filters returns ``True``. Behaves like ``or`` between filters.

    >>> any_(contains("Hello"), regex(r"^World"))
    """
    return lambda wa, m: any(f(wa, m) for f in filters)


def not_(fil: Callable[[_Wa, _T], bool]) -> Callable[[_Wa, _T], bool]:
    """
    Negates the given filter. Behaves like ``not``

    >>> not_(contains("Hello"))
    """
    return lambda wa, m: not fil(wa, m)


def sent_to(*, display_phone_number: str = None, phone_number_id: str = None):
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
    return lambda _, m: (
        m.metadata.display_phone_number == display_phone_number
        if display_phone_number
        else m.metadata.phone_number_id == phone_number_id
    )


sent_to_me: _MessageFilterT = lambda wa, m: sent_to(phone_number_id=wa.phone_id)(wa, m)
"""
Filter for updates that are sent to the client phone number.

- Use this filter when you choose not filter updates (e.g. ``WhatsApp(..., filter_updates=False)``) so you can still filter for messages that are sent to the client phone number.

>>> sent_to_me
"""


def from_users(
    *numbers: str,
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for messages that are sent from the given numbers.

    >>> from_users("+1 555-555-5555", "972123456789")
    """
    only_nums_pattern = re.compile(r"\D")
    numbers = tuple(re.sub(only_nums_pattern, "", n) for n in numbers)
    return lambda _, m: m.from_user.wa_id in numbers


def from_countries(
    *prefixes: str | int,
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for messages that are sent from the given country codes.

    - See https://countrycode.org/ for a list of country codes.

    It is always recommended to restrict the countries that can use your bot. remember that you pay for
    every conversation that you reply to.

    >>> from_countries("972", "1") # Israel and USA
    """
    codes = tuple(str(p) for p in prefixes)
    return lambda _, m: m.from_user.wa_id.startswith(codes)


def matches(
    *strings: str, ignore_case: bool = False
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for messages that are matching (``==``) any of the given strings.

    The strings will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``

    >>> matches("Hello", "Hi")

    Args:
        *strings: The strings to match.
        ignore_case: Whether to ignore case when matching.
    """
    strings = tuple(m.lower() for m in strings) if ignore_case else strings
    return (
        lambda _, m: any(
            (txt.lower() if ignore_case else txt) in strings
            for txt_field in m._txt_fields
            if (txt := getattr(m, txt_field)) is not None
        )
        if getattr(m, "_txt_fields", None)
        else False
    )


def startswith(
    *prefixes: str, ignore_case: bool = False
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for updates that start with any of the given prefixes.

    The prefixes will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``

    >>> startswith("Hello", "Hi", ignore_case=True)

    Args:
        *prefixes: The prefixes to match.
        ignore_case: Whether to ignore case when matching.
    """
    prefixes = tuple(m.lower() for m in prefixes) if ignore_case else prefixes
    return (
        lambda _, u: any(
            (txt.lower() if ignore_case else txt).startswith(prefixes)
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False
    )


def endswith(
    *suffixes: str, ignore_case: bool = False
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for updates that end with any of the given suffixes.

    The suffixes will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``

    >>> endswith("Hello", "Hi", ignore_case=True)

    Args:
        *suffixes: The suffixes to match.
        ignore_case: Whether to ignore case when matching.
    """
    suffixes = tuple(m.lower() for m in suffixes) if ignore_case else suffixes
    return (
        lambda _, u: any(
            (txt.lower() if ignore_case else txt).endswith(suffixes)
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False
    )


def contains(
    *words: str, ignore_case: bool = False
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for updates that contain any of the given words.

    The words will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``

    >>> contains("Hello", "Hi", ignore_case=True)

    Args:
        *words: The words to match.
        ignore_case: Whether to ignore case when matching.
    """
    words = tuple(m.lower() for m in words) if ignore_case else words
    return (
        lambda _, u: any(
            word in (txt.lower() if ignore_case else txt)
            for word in words
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False
    )


def regex(
    *patterns: str | re.Pattern, flags: int = 0
) -> _MessageFilterT | _CallbackFilterT | _MessageStatusFilterT:
    """
    Filter for updates that match any of the given regex patterns.

    The patterns will be checked against the following fields:
        - :class:`Message`: ``text``, ``caption``
        - :class:`CallbackButton`: ``data``
        - :class:`CallbackSelection`: ``data``
        - :class:`MessageStatus`: ``tracker``

    >>> regex(r"Hello|Hi")

    Args:
        *patterns: The regex patterns to match.
        flags: The regex flags to use.
    """
    patterns = tuple(
        p if isinstance(p, re.Pattern) else re.compile(p, flags) for p in patterns
    )
    return (
        lambda _, u: any(
            re.match(p, txt)
            for p in patterns
            for txt_field in u._txt_fields
            if (txt := getattr(u, txt_field)) is not None
        )
        if getattr(u, "_txt_fields", None)
        else False
    )


class _BaseUpdateFilters(abc.ABC):
    """
    Base class for all filters.
    """

    def __new__(cls, wa: _Wa, m: _T) -> bool:
        """When instantiated, call the ``any`` method."""
        return cls.any(wa, m)

    @property
    @abc.abstractmethod
    def __message_types__(self) -> tuple[_Mt, ...]:
        """The message types that the filter is for."""
        ...

    @staticmethod
    @abc.abstractmethod
    def any(wa: _Wa, m: _T) -> bool:
        """Filter for all updates of this type."""
        ...

    @classmethod
    def _match_type(cls, m: _Msg) -> bool:
        return m.type in cls.__message_types__


class _MediaFilters(_BaseUpdateFilters):
    """
    Useful filters for media messages. Alias: ``filters.media``.
    """

    __message_types__ = (
        _Mt.IMAGE,
        _Mt.VIDEO,
        _Mt.AUDIO,
        _Mt.DOCUMENT,
        _Mt.STICKER,
    )

    any: _MessageFilterT = lambda _, m: m.has_media
    """
    Filter for all media messages.
        - Same as ``filters.media``.

    >>> filters.media.any
    """

    @classmethod
    def mimetypes(cls, *mimetypes: str) -> _MessageFilterT:
        """
        Filter for media messages that match any of the given mime types.

        - `Supported Media Types on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types>`_.

        >>> media.mimetypes("application/pdf", "image/png")
        >>> video.mimetypes("video/mp4")
        >>> audio.mimetypes("audio/mpeg")
        """
        return lambda _, m: cls._match_type(m) and m.media.mime_type in mimetypes

    @classmethod
    def extensions(cls, *extensions: str) -> _MessageFilterT:
        """
        Filter for media messages that match any of the given extensions.

        >>> media.extensions(".pdf", ".png")
        >>> video.extensions(".mp4")
        >>> document.extensions(".pdf")
        """
        return lambda _, m: cls._match_type(m) and m.media.extension in extensions


media: _MessageFilterT | type[_MediaFilters] = _MediaFilters


class _MediaWithCaptionFilters(_MediaFilters, abc.ABC):
    @classmethod
    def _has_caption(cls, _: _Wa, m: _Msg) -> bool:
        return cls._match_type(m) and m.caption is not None

    has_caption: _MessageFilterT = _has_caption
    """
    Filter for media messages that have a caption.

    >>> filters.image.has_caption
    >>> filters.video.has_caption
    """


class _TextFilters(_BaseUpdateFilters):
    """Useful filters for text messages. Alias: ``filters.text``."""

    __message_types__ = (_Mt.TEXT,)

    any: _MessageFilterT = lambda _, m: m.type == _Mt.TEXT
    """
    Filter for all text messages.
        - Same as ``filters.text``.

    >>> filters.text.any
    """

    is_command: _MessageFilterT = lambda _, m: m.type == _Mt.TEXT and m.text.startswith(
        ("/", "!", "#")
    )
    """
    Filter for text messages that are commands (start with ``/``, ``!``, or ``#``).
        - Use text.command(...) if you want to filter for specific commands or prefixes.

    >>> filters.text.is_command
    """

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.matches(...)")
    def matches(*strings: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.matches(...)`` instead."""
        return lambda _, m: _TextFilters._match_type(m) and matches(
            *strings, ignore_case=ignore_case
        )

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.contains(...)")
    def contains(*words: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.contains(...)`` instead."""
        return lambda _, m: _TextFilters._match_type(m) and contains(
            *words, ignore_case=ignore_case
        )

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.startswith(...)")
    def startswith(*prefixes: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.startswith(...)`` instead."""
        return lambda _, m: _TextFilters._match_type(m) and startswith(
            *prefixes, ignore_case=ignore_case
        )

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.endswith(...)")
    def endswith(*suffixes: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.endswith(...)`` instead."""
        return lambda _, m: _TextFilters._match_type(m) and endswith(
            *suffixes, ignore_case=ignore_case
        )

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.regex(...)")
    def regex(*patterns: None, flags: None = 0) -> None:
        """Deprecated. Use ``filters.regex(...)`` instead."""
        return lambda _, m: _TextFilters._match_type(m) and regex(
            *patterns, flags=flags
        )

    @staticmethod
    def length(*lengths: tuple[int, int]) -> _MessageFilterT:
        """
        Filter for text messages that have a length between any of the given ranges.

        >>> text.length((1, 10), (50, 100))

        Args:
            *lengths: The length range/s to filter for (e.g. (1, 10), (50, 100)).
        """
        return lambda _, m: _TextFilters._match_type(m) and any(
            i[0] <= len(m.text) <= i[1] for i in lengths
        )

    @staticmethod
    def command(
        *cmds: str,
        prefixes: str | Iterable[str] = "/!",
        ignore_case: bool = False,
    ) -> _MessageFilterT:
        """
        Filter for text messages that are commands.

        >>> text.command("start", "hello", prefixes="/", ignore_case=True)

        Args:
            *cmds: The command/s to filter for (e.g. "start", "hello").
            prefixes: The prefix/s to filter for (default: "/!", i.e. "/start").
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        cmds = tuple(c.lower() for c in cmds) if ignore_case else cmds
        return lambda _, m: _TextFilters._match_type(m) and (
            m.text[0] in prefixes
            and (m.text[1:].lower() if ignore_case else m.text[1:]).startswith(cmds)
        )


text: _MessageFilterT | type[_TextFilters] = _TextFilters


class _ImageFilters(_MediaWithCaptionFilters):
    """Useful filters for image messages. Alias: ``filters.image``."""

    __message_types__ = (_Mt.IMAGE,)

    any: _MessageFilterT = lambda _, m: _ImageFilters._match_type(m)
    """
    Filter for all image messages.
        - Same as ``filters.image``.

    >>> filters.image.any
    """


image: _MessageFilterT | type[_ImageFilters] = _ImageFilters


class _VideoFilters(_MediaWithCaptionFilters):
    """Useful filters for video messages. Alias: ``filters.video``."""

    __message_types__ = (_Mt.VIDEO,)

    any: _MessageFilterT = lambda _, m: _VideoFilters._match_type(m)
    """
    Filter for all video messages.
        - Same as ``filters.video``.

    >>> filters.video.any
    """


video: _MessageFilterT | type[_VideoFilters] = _VideoFilters


class _DocumentFilters(_MediaWithCaptionFilters):
    """Useful filters for document messages. Alias: ``filters.document``."""

    __message_types__ = (_Mt.DOCUMENT,)

    any: _MessageFilterT = lambda _, m: _DocumentFilters._match_type(m)
    """
    Filter for all document messages.
        - Same as ``filters.document``.

    >>> filters.document.any
    """


document: _MessageFilterT | type[_DocumentFilters] = _DocumentFilters


class _AudioFilters(_MediaFilters):
    """Useful filters for audio messages. Alias: ``filters.audio``."""

    __message_types__ = (_Mt.AUDIO,)

    any: _MessageFilterT = lambda _, m: _AudioFilters._match_type(m)
    """
    Filter for all audio messages (voice notes and audio files).
        - Same as ``filters.audio``.

    >>> filters.audio.any
    """

    voice: _MessageFilterT = lambda _, m: _AudioFilters._match_type(m) and m.audio.voice
    """
    Filter for audio messages that are voice notes.

    >>> filters.audio.voice
    """

    audio: _MessageFilterT = (
        lambda _, m: _AudioFilters._match_type(m) and not m.audio.voice
    )
    """
    Filter for audio messages that are audio files.

    >>> filters.audio.audio
    """


audio: _MessageFilterT | type[_AudioFilters] = _AudioFilters


class _StickerFilters(_MediaFilters):
    """Useful filters for sticker messages. Alias: ``filters.sticker``."""

    __message_types__ = (_Mt.STICKER,)

    any: _MessageFilterT = lambda _, m: _StickerFilters._match_type(m)
    """
    Filter for all sticker messages.
        - Same as ``filters.sticker``.

    >>> filters.sticker.any
    """

    animated: _MessageFilterT = (
        lambda _, m: _StickerFilters._match_type(m) and m.sticker.animated
    )
    """
    Filter for animated sticker messages.

    >>> filters.sticker.animated
    """

    static: _MessageFilterT = (
        lambda _, m: _StickerFilters._match_type(m) and not m.sticker.animated
    )
    """
    Filter for static sticker messages.

    >>> filters.sticker.static
    """


sticker: _MessageFilterT | type[_StickerFilters] = _StickerFilters


class _LocationFilters(_BaseUpdateFilters):
    """Useful filters for location messages. Alias: ``filters.location``."""

    __message_types__ = (_Mt.LOCATION,)

    any: _MessageFilterT = lambda _, m: _LocationFilters._match_type(m)
    """
    Filter for all location messages.
        - Same as ``filters.location``.

    >>> filters.location.any
    """

    current_location: _MessageFilterT = (
        lambda _, m: _LocationFilters._match_type(m) and m.location.current_location
    )
    """
    Filter for location messages that are the current location of the user and not just selected manually.

    >>> filters.location.current_location
    """

    @staticmethod
    def in_radius(lat: float, lon: float, radius: float | int) -> _MessageFilterT:
        """
        Filter for location messages that are in a given radius.

        >>> location.in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

        Args:
            lat: Latitude of the center of the radius.
            lon: Longitude of the center of the radius.
            radius: Radius in kilometers.
        """

        def _in_radius(_: _Wa, msg: _Msg) -> bool:
            return _LocationFilters._match_type(msg) and msg.location.in_radius(
                lat=lat, lon=lon, radius=radius
            )

        return _in_radius


location: _MessageFilterT | type[_LocationFilters] = _LocationFilters


class _ReactionFilters(_BaseUpdateFilters):
    """Useful filters for reaction messages. Alias: ``filters.reaction``."""

    __message_types__ = (_Mt.REACTION,)

    any: _MessageFilterT = lambda _, m: _ReactionFilters._match_type(m)
    """
    Filter for all reaction updates (added or removed).
        - Same as ``filters.reaction``.

    >>> filters.reaction.any
    """

    added: _MessageFilterT = (
        lambda _, m: _ReactionFilters._match_type(m) and m.reaction.emoji is not None
    )
    """
    Filter for reaction messages that were added.

    >>> filters.reaction.added
    """

    removed: _MessageFilterT = (
        lambda _, m: _ReactionFilters._match_type(m) and m.reaction.emoji is None
    )
    """
    Filter for reaction messages that were removed.

    >>> filters.reaction.removed
    """

    @staticmethod
    def emojis(*emojis: str) -> _MessageFilterT:
        """
        Filter for custom reaction messages. pass emojis as strings.

        >>> reaction.emojis("👍","👎")
        """
        return (
            lambda _, m: _ReactionFilters._match_type(m) and m.reaction.emoji in emojis
        )


reaction: _MessageFilterT | type[_ReactionFilters] = _ReactionFilters


class _ContactsFilters(_BaseUpdateFilters):
    """Useful filters for contact messages. Alias: ``filters.contacts``."""

    __message_types__ = (_Mt.CONTACTS,)

    any: _MessageFilterT = lambda _, m: _ContactsFilters._match_type(m)
    """
    Filter for all contacts messages.
        - Same as ``filters.contacts``.

    >>> filters.contacts.any
    """

    has_wa: _MessageFilterT = lambda _, m: _ContactsFilters._match_type(m) and (
        any(
            (
                p.wa_id
                for p in (phone for contact in m.contacts for phone in contact.phones)
            )
        )
    )
    """
    Filter for contacts messages that have a WhatsApp account.

    >>> filters.contacts.has_wa
    """

    @staticmethod
    def count(min_count: int, max_count: int) -> _MessageFilterT:
        """
        Filter for contacts messages that have a number of contacts between min_count and max_count.

        >>> contacts.count(1, 1) # ensure only 1 contact
        >>> contacts.count(1, 5) # between 1 and 5 contacts
        """
        return (
            lambda _, m: _ContactsFilters._match_type(m)
            and min_count <= len(m.contacts) <= max_count
        )

    @staticmethod
    def phones(*phones: str) -> _MessageFilterT:
        """
        Filter for contacts messages that have the given phone number/s.

        >>> contacts.phones("+1 555-555-5555","972123456789")
        """
        only_nums_pattern = re.compile(r"\D")
        phones = [re.sub(only_nums_pattern, "", p) for p in phones]
        return lambda _, m: _ContactsFilters._match_type(m) and (
            any(
                re.sub(only_nums_pattern, "", p.phone) in phones
                for contact in m.contacts
                for p in contact.phones
            )
        )


contacts: _MessageFilterT | type[_ContactsFilters] = _ContactsFilters


class _OrderFilters(_BaseUpdateFilters):
    """Useful filters for order messages. Alias: ``filters.order``."""

    __message_types__ = (_Mt.ORDER,)

    any: _MessageFilterT = lambda _, m: _OrderFilters._match_type(m)
    """
    Filter for all order messages.
        - Same as ``filters.order``.

    >>> filters.order.any
    """

    @staticmethod
    def price(min_price: float, max_price: float) -> _MessageFilterT:
        """
        Filter for order messages that have a total price between min_price and max_price.

        Args:
            min_price: Minimum price.
            max_price: Maximum price.

        >>> order.price(1, 100) # total price between 1 and 100
        """
        return (
            lambda _, m: _OrderFilters._match_type(m)
            and min_price <= m.order.total_price <= max_price
        )

    @staticmethod
    def count(min_count: int, max_count: int) -> _MessageFilterT:
        """
        Filter for order messages that have a number of items between min_count and max_count.

        Args:
            min_count: Minimum number of items.
            max_count: Maximum number of items.

        >>> order.count(1, 5) # between 1 and 5 items
        """
        return (
            lambda _, m: _OrderFilters._match_type(m)
            and min_count <= len(m.order.products) <= max_count
        )

    @staticmethod
    def has_product(*skus: str) -> _MessageFilterT:
        """
        Filter for order messages that have the given product/s.

        Args:
            *skus: The products SKUs.

        >>> order.has_product("pizza_1","pizza_2")
        """
        return lambda _, m: _OrderFilters._match_type(m) and (
            any(p.sku in skus for p in m.order.products)
        )


order: _MessageFilterT | type[_OrderFilters] = _OrderFilters


class _UnsupportedMsgFilters(_BaseUpdateFilters):
    """Useful filters for unsupported messages. Alias: ``filters.unsupported``."""

    __message_types__ = (_Mt.UNSUPPORTED,)

    any: _MessageFilterT = lambda _, m: m.type == _Mt.UNSUPPORTED
    """
    Filter for all unsupported messages.
        - Same as ``filters.unsupported``.

    >>> filters.unsupported.any
    """


unsupported: _MessageFilterT | type[_UnsupportedMsgFilters] = _UnsupportedMsgFilters


class _CallbackFilters(_BaseUpdateFilters):
    """Useful filters for callback queries. Alias: ``filters.callback``."""

    __message_types__ = (_Mt.INTERACTIVE,)

    def __new__(cls):
        return cls.any

    any: _CallbackFilterT = lambda _, __: True
    """
    Filter for all callback queries (the default).
        - Same as ``filters.callback``.

    >>> filters.callback.any
    """

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.matches(...)")
    def data_matches(*strings: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.matches(...)`` instead."""
        return matches(*strings, ignore_case=ignore_case)

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.data_startswith(...)")
    def data_startswith(*prefixes: None, ignore_case: None = False) -> None:
        """Deprecated. Use ``filters.startswith(...)`` instead."""
        return startswith(*prefixes, ignore_case=ignore_case)

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.data_endswith(...)")
    def data_endswith(*suffixes: None, ignore_case: bool = None) -> None:
        """Deprecated. Use ``filters.endswith(...)`` instead."""
        return endswith(*suffixes, ignore_case=ignore_case)

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.data_contains(...)")
    def data_contains(*words: None, ignore_case: bool = None) -> None:
        """Deprecated. Use ``filters.contains(...)`` instead."""
        return contains(*words, ignore_case=ignore_case)

    @staticmethod
    @_utils.deprecated_func(use_instead="filters.data_regex(...)")
    def data_regex(*patterns: None, flags: None = 0) -> None:
        """Deprecated. Use ``filters.regex(...)`` instead."""
        return regex(*patterns, flags=flags)


callback: _CallbackFilterT | type[_CallbackFilters] = _CallbackFilters


class _MessageStatusFilters(_BaseUpdateFilters):
    """Useful filters for message status updates. Alias: ``filters.message_status``."""

    __message_types__ = ()

    any: _MessageStatusFilterT = lambda _, __: True
    """
    Filter for all message status updates (the default).
        - Same as ``filters.message_status``.

    >>> filters.message_status.any
    """

    sent: _MessageStatusFilterT = lambda _, s: s.status == _Mst.SENT
    """
    Filter for messages that have been sent.

    >>> filters.message_status.sent
    """

    delivered: _MessageStatusFilterT = lambda _, s: s.status == _Mst.DELIVERED
    """
    Filter for messages that have been delivered.

    >>> filters.message_status.delivered
    """

    read: _MessageStatusFilterT = lambda _, s: s.status == _Mst.READ
    """
    Filter for messages that have been read.

    >>> filters.message_status.read
    """

    failed: _MessageStatusFilterT = lambda _, s: s.status == _Mst.FAILED
    """
    Filter for status updates of messages that have failed to send.

    >>> filters.message_status.failed
    """

    @staticmethod
    def failed_with(
        *errors: type[WhatsAppError] | int,
    ) -> _MessageStatusFilterT:
        """
        Filter for status updates of messages that have failed to send with the given error/s.

        Args:
            *errors: The exceptions from :mod:`pywa.errors` or error codes to match.

        >>> message_status.failed_with(ReEngagementMessage)
        >>> message_status.failed_with(131051)
        """
        error_codes = tuple(c for c in errors if isinstance(c, int))
        exceptions = tuple(
            e for e in errors if e not in error_codes and issubclass(e, WhatsAppError)
        )
        return lambda _, s: s.status == _Mst.FAILED and (
            any((isinstance(s.error, e) for e in exceptions))
            or s.error.error_code in error_codes
        )

    with_tracker: _MessageStatusFilterT = lambda _, s: s.tracker is not None
    """
    Filter for messages that sent with tracker

    >>> filters.message_status.with_tracker
    """


message_status: _MessageStatusFilterT | type[_MessageStatusFilters] = (
    _MessageStatusFilters
)


class _TemplateStatusFilters(_BaseUpdateFilters):
    """Useful filters for template status updates. Alias: ``filters.template_status``."""

    __message_types__ = ()

    any: _TemplateStatusFilterT = lambda _, __: True
    """
    Filter for all template status updates (the default).
        - Same as ``filters.template_status``.

    >>> filters.template_status.any
    """

    template_name: lambda name: _TemplateStatusFilterT = (
        lambda name: lambda _, s: s.template_name == name
    )
    """
    Filter for template status updates that are for the given template name.

    >>> template_status.template_name("my_template")
    """

    @staticmethod
    def on_event(*events: _Ts.TemplateEvent) -> _TemplateStatusFilterT:
        """
        Filter for template status updates that are for the given event/s.

        Args:
            *events: The template events to filter for.

        >>> template_status.on_event(_Ts.TemplateEvent.APPROVED)
        """
        return lambda _, s: s.event in events

    @staticmethod
    def on_rejection_reason(
        *reasons: _Ts.TemplateRejectionReason,
    ) -> _TemplateStatusFilterT:
        """
        Filter for template status updates that are for the given reason/s.

        Args:
            *reasons: The template reasons to filter for.

        >>> template_status.on_rejection_reason(_Ts.TemplateRejectionReason.INCORRECT_CATEGORY)
        """
        return lambda _, s: s.reason in reasons


template_status: _TemplateStatusFilterT | type[_TemplateStatusFilters] = (
    _TemplateStatusFilters
)
