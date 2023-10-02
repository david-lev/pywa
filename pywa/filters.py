"""Usefully filters to use in your handlers."""
from __future__ import annotations

__all__ = [
    "all_",
    "any_",
    "not_",
    "forwarded",
    "forwarded_many_times",
    "reply",
    "from_users",
    "from_countries",
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

import re
from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING, Iterable, TypeVar, TypeAlias, Type
from pywa import utils
from pywa.errors import WhatsAppError, ReEngagementMessage
from pywa.types import MessageType as Mt, Message as Msg, MessageStatus as Ms, MessageStatusType as Mst, \
    CallbackButton, CallbackSelection, TemplateStatus as Ts
from pywa.types.base_update import BaseUpdate

if TYPE_CHECKING:
    from pywa import WhatsApp as Wa

    MessageFilterT: TypeAlias = Callable[[Wa, Msg], bool]
    CallbackFilterT: TypeAlias = Callable[[Wa, CallbackButton | CallbackSelection], bool]
    MessageStatusFilterT: TypeAlias = Callable[[Wa, Ms], bool]
    TemplateStatusFilterT: TypeAlias = Callable[[Wa, Ts], bool]

T = TypeVar("T", bound=BaseUpdate)

forwarded: MessageFilterT = lambda _, m: m.forwarded  # Filter for forwarded messages.
"""
Filter for forwarded messages.

>>> filters.forwarded
"""

forwarded_many_times: MessageFilterT = lambda _, m: m.forwarded_many_times
"""
Filter for messages that have been forwarded many times.

>>> filters.forwarded_many_times
"""

reply: MessageFilterT = lambda _, m: m.reply_to_message is not None
"""
Filter for messages that reply to another message.

>>> filters.reply
"""


def all_(*filters: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that pass all the given filters.

    >>> all_(text.startswith("Hello"), text.endswith("Word"))
    """
    return lambda wa, m: all(f(wa, m) for f in filters)


def any_(*filters: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that pass any of the given filters.

    >>> any_(text.contains("Hello"), text.regex(r"^World"))
    """
    return lambda wa, m: any(f(wa, m) for f in filters)


def not_(fil: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that don't pass the given filter.

    >>> not_(text.contains("Hello"))
    """
    return lambda wa, m: not fil(wa, m)


def from_users(*numbers: str) -> MessageFilterT | CallbackFilterT | MessageStatusFilterT:
    """
    Filter for messages that are sent from the given numbers.

    >>> from_users("+1 555-555-5555", "972123456789")
    """
    only_nums_pattern = re.compile(r"\D")
    numbers = tuple(re.sub(only_nums_pattern, "", n) for n in numbers)
    return lambda _, m: m.from_user.wa_id in numbers


def from_countries(*prefixes: str | int) -> MessageFilterT | CallbackFilterT | MessageStatusFilterT:
    """
    Filter for messages that are sent from the given country codes.

    - See https://countrycode.org/ for a list of country codes.

    It is always recommended to restrict the countries that can use your bot. remember that you pay for
    every conversation that you reply to.

    >>> from_countries("972", "1") # Israel and USA
    """
    codes = tuple(str(p) for p in prefixes)
    return lambda _, m: m.from_user.wa_id.startswith(codes)


class _BaseUpdateFilter(ABC):
    """
    Base class for all filters.
    """

    def __new__(cls, wa: Wa, m: T) -> bool:
        """When instantiated, call the ``any`` method."""
        return cls.any(wa, m)

    @property
    @abstractmethod
    def __message_types__(self) -> tuple[Mt, ...]:
        """The message types that the filter is for."""
        ...

    @staticmethod
    @abstractmethod
    def any(wa: Wa, m: T) -> bool:
        """Filter for all updates of this type."""
        ...

    @classmethod
    def _match_type(cls, m: Msg) -> bool:
        return m.type in cls.__message_types__


class MediaFilter(_BaseUpdateFilter):
    """
    Useful filters for media messages. Alias: ``filters.media``.
    """
    __message_types__ = (Mt.IMAGE, Mt.VIDEO, Mt.AUDIO, Mt.DOCUMENT, Mt.STICKER)

    any: MessageFilterT = lambda _, m: m.has_media
    """
    Filter for all media messages.
        - Same as ``filters.media``.
    
    >>> filters.media.any
    """

    @classmethod
    def mimetypes(cls, *mimetypes: str) -> MessageFilterT:
        """
        Filter for media messages that match any of the given mime types.

        - `\`Supported Media Types\` on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types>`_.

        >>> media.mimetypes("application/pdf", "image/png")
        >>> video.mimetypes("video/mp4")
        >>> audio.mimetypes("audio/mpeg")
        """
        return lambda _, m: cls._match_type(m) and any(
            t == getattr(m, cls.__message_types__[0].value).mime_type for t in mimetypes
        )


media: MessageFilterT | Type[MediaFilter] = MediaFilter


class _MediaWithCaptionFilter(MediaFilter, ABC):
    @classmethod
    def _has_caption(cls, _: Wa, m: Msg) -> bool:
        return cls._match_type(m) and m.caption is not None

    has_caption: MessageFilterT = _has_caption
    """
    Filter for media messages that have a caption.
    
    >>> filters.media.has_caption
    """


class TextFilter(_BaseUpdateFilter):
    """Useful filters for text messages. Alias: ``filters.text``."""

    __message_types__ = (Mt.TEXT,)

    any: MessageFilterT = lambda _, m: m.type == Mt.TEXT
    """
    Filter for all text messages.
        - Same as ``filters.text``.
    
    >>> filters.text.any
    """

    is_command: MessageFilterT = lambda _, m: m.type == Mt.TEXT and m.text.startswith(("!", "/", "#"))
    """
    Filter for text messages that are commands (start with ``!``, ``/``, or ``#``).
        - Use TextFilter.command if you want to filter for specific commands or prefixes.
    
    >>> filters.text.is_command
    """

    @staticmethod
    def matches(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that match exactly the given text/s.

        >>> text.matches("Hello","Hi")

        Args:
            *matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text) in matches

    @staticmethod
    def contains(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that contain the given text/s.

        >>> text.contains("Cat","Dog",ignore_case=True)

        Args:
            *matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching. (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, m: TextFilter._match_type(m) and any(
            t in (m.text.lower() if ignore_case else m.text) for t in matches
        )

    @staticmethod
    def startswith(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that start with the given text/s.

        >>> text.startswith("What", "When", ignore_case=True)

        Args:
            *matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text).startswith(
            matches)

    @staticmethod
    def endswith(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that end with the given text/s.

        >>> text.endswith("Bye", "See you", ignore_case=True)

        Args:
            *matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text).endswith(matches)

    @staticmethod
    def regex(*patterns: str | re.Pattern, flags: int = 0) -> MessageFilterT:
        """
        Filter for text messages that match the given regex/regexes.

        >>> text.regex(r"Hello\s+World", r"Bye\s+World", flags=re.IGNORECASE)

        Args:
            *patterns: The regex/regexes to filter for.
            flags: The regex flags to use (default: ``0``).
        """
        patterns = tuple(re.compile(p, flags) if isinstance(p, str) else p for p in patterns)
        return lambda _, m: TextFilter._match_type(m) and any(re.match(p, m.text, flags) for p in patterns)

    @staticmethod
    def length(*lengths: tuple[int, int]) -> MessageFilterT:
        """
        Filter for text messages that have a length between the given range/s.

        >>> text.length((1, 10), (50, 100))

        Args:
            *lengths: The length range/s to filter for (e.g. (1, 10), (50, 100)).
        """
        return lambda _, m: TextFilter._match_type(m) and any(i[0] <= len(m.text) <= i[1] for i in lengths)

    @staticmethod
    def command(*cmds: str, prefixes: str | Iterable[str] = "!", ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that are commands.

        >>> text.command("start", "hello", prefixes=("!", "/"), ignore_case=True)

        Args:
            *cmds: The command/s to filter for (e.g. "start", "hello").
            prefixes: The prefix/s to filter for (default: "!", i.e. "!start").
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        cmds = tuple(c.lower() for c in cmds) if ignore_case else cmds
        return lambda _, m: TextFilter._match_type(m) and (
                m.text[0] in prefixes and (m.text[1:].lower() if ignore_case else m.text[1:]).startswith(cmds)
        )


text: MessageFilterT | Type[TextFilter] = TextFilter


class ImageFilter(_MediaWithCaptionFilter):
    """Useful filters for image messages. Alias: ``filters.image``."""

    __message_types__ = (Mt.IMAGE,)

    any: MessageFilterT = lambda _, m: ImageFilter._match_type(m)
    """
    Filter for all image messages.
        - Same as ``filters.image``.
    
    >>> filters.image.any
    """


image: MessageFilterT | Type[ImageFilter] = ImageFilter


class VideoFilter(_MediaWithCaptionFilter):
    """Useful filters for video messages. Alias: ``filters.video``."""

    __message_types__ = (Mt.VIDEO,)

    any: MessageFilterT = lambda _, m: VideoFilter._match_type(m)
    """
    Filter for all video messages.
        - Same as ``filters.video``.
    
    >>> filters.video.any
    """


video: MessageFilterT | Type[VideoFilter] = VideoFilter


class DocumentFilter(_MediaWithCaptionFilter):
    """Useful filters for document messages. Alias: ``filters.document``."""

    __message_types__ = (Mt.DOCUMENT,)

    any: MessageFilterT = lambda _, m: DocumentFilter._match_type(m)
    """
    Filter for all document messages.
        - Same as ``filters.document``.
    
    >>> filters.document.any
    """


document: MessageFilterT | Type[DocumentFilter] = DocumentFilter


class AudioFilter(MediaFilter):
    """Useful filters for audio messages. Alias: ``filters.audio``."""

    __message_types__ = (Mt.AUDIO,)

    any: MessageFilterT = lambda _, m: AudioFilter._match_type(m)
    """
    Filter for all audio messages (voice notes and audio files).
        - Same as ``filters.audio``.
    
    >>> filters.audio.any
    """

    voice: MessageFilterT = lambda _, m: AudioFilter._match_type(m) and m.audio.voice
    """
    Filter for audio messages that are voice notes.
    
    >>> filters.audio.voice
    """

    audio: MessageFilterT = lambda _, m: AudioFilter._match_type(m) and not m.audio.voice
    """
    Filter for audio messages that are audio files.
    
    >>> filters.audio.audio
    """


audio: MessageFilterT | Type[AudioFilter] = AudioFilter


class StickerFilter(MediaFilter):
    """Useful filters for sticker messages. Alias: ``filters.sticker``."""

    __message_types__ = (Mt.STICKER,)

    any: MessageFilterT = lambda _, m: StickerFilter._match_type(m)
    """
    Filter for all sticker messages.
        - Same as ``filters.sticker``.
    
    >>> filters.sticker.any
    """

    animated: MessageFilterT = lambda _, m: StickerFilter._match_type(m) and m.sticker.animated
    """
    Filter for animated sticker messages.
    
    >>> filters.sticker.animated
    """

    static: MessageFilterT = lambda _, m: StickerFilter._match_type(m) and not m.sticker.animated
    """
    Filter for static sticker messages.
    
    >>> filters.sticker.static
    """


sticker: MessageFilterT | Type[StickerFilter] = StickerFilter


class LocationFilter(_BaseUpdateFilter):
    """Useful filters for location messages. Alias: ``filters.location``."""

    __message_types__ = (Mt.LOCATION,)

    any: MessageFilterT = lambda _, m: LocationFilter._match_type(m)
    """
    Filter for all location messages.
        - Same as ``filters.location``.
    
    >>> filters.location.any
    """

    current_location: MessageFilterT = lambda _, m: LocationFilter._match_type(m) and m.location.current_location
    """
    Filter for location messages that are the current location of the user and not just selected manually.
    
    >>> filters.location.current_location
    """

    @staticmethod
    def in_radius(lat: float, lon: float, radius: float | int) -> MessageFilterT:
        """
        Filter for location messages that are in a given radius.

        >>> location.in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

        Args:
            lat: Latitude of the center of the radius.
            lon: Longitude of the center of the radius.
            radius: Radius in kilometers.
        """

        def _in_radius(_: Wa, msg: Msg) -> bool:
            return LocationFilter._match_type(msg) and \
                utils.get_distance(
                    lat1=lat, lon1=lon, lat2=msg.location.latitude, lon2=msg.location.longitude
                ) <= radius

        return _in_radius


location: MessageFilterT | Type[LocationFilter] = LocationFilter


class ReactionFilter(_BaseUpdateFilter):
    """Useful filters for reaction messages. Alias: ``filters.reaction``."""

    __message_types__ = (Mt.REACTION,)

    any: MessageFilterT = lambda _, m: ReactionFilter._match_type(m)
    """
    Filter for all reaction updates (added or removed).
        - Same as ``filters.reaction``.
    
    >>> filters.reaction.any
    """

    added: MessageFilterT = lambda _, m: ReactionFilter._match_type(m) and m.reaction.emojis is not None
    """
    Filter for reaction messages that were added.
    
    >>> filters.reaction.added
    """

    removed: MessageFilterT = lambda _, m: ReactionFilter._match_type(m) and m.reaction.emojis is None
    """
    Filter for reaction messages that were removed.
    
    >>> filters.reaction.removed
    """

    @staticmethod
    def emojis(*emojis: str) -> MessageFilterT:
        """
        Filter for custom reaction messages. pass emojis as strings.

        >>> reaction.emojis("👍","👎")
        """
        return lambda _, m: ReactionFilter._match_type(m) and m.reaction.emoji in emojis


reaction: MessageFilterT | Type[ReactionFilter] = ReactionFilter


class ContactsFilter(_BaseUpdateFilter):
    """Useful filters for contact messages. Alias: ``filters.contacts``."""

    __message_types__ = (Mt.CONTACTS,)

    any: MessageFilterT = lambda _, m: ContactsFilter._match_type(m)
    """
    Filter for all contacts messages.
        - Same as ``filters.contacts``.
    
    >>> filters.contacts.any
    """

    has_wa: MessageFilterT = lambda _, m: ContactsFilter._match_type(m) and (
        any((p.wa_id for p in (phone for contact in m.contacts for phone in contact.phones)))
    )
    """
    Filter for contacts messages that have a WhatsApp account.
    
    >>> filters.contacts.has_wa
    """

    @staticmethod
    def count(min_count: int, max_count: int) -> MessageFilterT:
        """
        Filter for contacts messages that have a number of contacts between min_count and max_count.

        >>> contacts.count(1, 1) # ensure only 1 contact
        >>> contacts.count(1, 5) # between 1 and 5 contacts
        """
        return lambda _, m: ContactsFilter._match_type(m) and min_count <= len(m.contacts) <= max_count

    @staticmethod
    def phones(*phones: str) -> MessageFilterT:
        """
        Filter for contacts messages that have the given phone number/s.

        >>> contacts.phones("+1 555-555-5555","972123456789")
        """
        only_nums_pattern = re.compile(r"\D")
        phones = [re.sub(only_nums_pattern, "", p) for p in phones]
        return lambda _, m: ContactsFilter._match_type(m) and (
            any(re.sub(only_nums_pattern, "", p.phones) in phones for contact in m.contacts for p in contact.phones)
        )


contacts: MessageFilterT | Type[ContactsFilter] = ContactsFilter


class OrderFilter(_BaseUpdateFilter):
    """Useful filters for order messages. Alias: ``filters.order``."""

    __message_types__ = (Mt.ORDER,)

    any: MessageFilterT = lambda _, m: OrderFilter._match_type(m)
    """
    Filter for all order messages.
        - Same as ``filters.order``.
    
    >>> filters.order.any
    """

    @staticmethod
    def price(min_price: float, max_price: float) -> MessageFilterT:
        """
        Filter for order messages that have a total price between min_price and max_price.

        Args:
            min_price: Minimum price.
            max_price: Maximum price.

        >>> order.price(1, 100) # total price between 1 and 100
        """
        return lambda _, m: OrderFilter._match_type(m) and min_price <= m.order.total_price <= max_price

    @staticmethod
    def count(min_count: int, max_count: int) -> MessageFilterT:
        """
        Filter for order messages that have a number of items between min_count and max_count.

        Args:
            min_count: Minimum number of items.
            max_count: Maximum number of items.

        >>> order.count(1, 5) # between 1 and 5 items
        """
        return lambda _, m: OrderFilter._match_type(m) and min_count <= len(m.order.products) <= max_count

    @staticmethod
    def has_product(*skus: str) -> MessageFilterT:
        """
        Filter for order messages that have the given product/s.

        Args:
            *skus: The products SKUs.

        >>> order.has_product("pizza_1","pizza_2")
        """
        return lambda _, m: OrderFilter._match_type(m) and (
            any(p.sku in skus for p in m.order.products)
        )


order: MessageFilterT | Type[OrderFilter] = OrderFilter


class UnsupportedMsgFilter(_BaseUpdateFilter):
    """Useful filters for unsupported messages. Alias: ``filters.unsupported``."""

    __message_types__ = (Mt.UNSUPPORTED,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda _, m: m.type == Mt.UNSUPPORTED
    """
    Filter for all unsupported messages.
        - Same as ``filters.unsupported``.
    
    >>> filters.unsupported.any
    """


unsupported: MessageFilterT | Type[UnsupportedMsgFilter] = UnsupportedMsgFilter


class CallbackFilter(_BaseUpdateFilter):
    """Useful filters for callback queries. Alias: ``filters.callback``."""

    __message_types__ = (Mt.INTERACTIVE,)

    def __new__(cls):
        return cls.any

    any: CallbackFilterT = lambda _, __: True
    """
    Filter for all callback queries (the default).
        - Same as ``filters.callback``.
    
    >>> filters.callback.any
    """

    @staticmethod
    def data_matches(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data match exactly the given string/s.

        >>> callback.data_matches("menu")
        >>> callback.data_matches("back","return","exit")

        Args:
            *matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, c: (c.data.lower() if ignore_case else c.data) in matches

    @staticmethod
    def data_startswith(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data starts with the given string/s.

        >>> callback.data_startswith("id:")

        Args:
            *matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, c: (c.data.lower() if ignore_case else c.data).startswith(matches)

    @staticmethod
    def data_endswith(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data ends with the given string/s.

        >>> callback.data_endswith(":true", ":false")

        Args:
            *matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, c: (c.data.lower() if ignore_case else c.data).endswith(matches)

    @staticmethod
    def data_contains(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data contains the given string/s.

        >>> callback.data_contains("back")

        Args:
            *matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda _, c: any((m in (c.data.lower() if ignore_case else c.data) for m in matches))

    @staticmethod
    def data_regex(*patterns: str | re.Pattern, flags: int = 0) -> CallbackFilterT:
        """
        Filter for callbacks their data matches the given regex/regexes.

        >>> callback.data_regex(r"^\d+$")  # only digits

        Args:
            *patterns: The regex/regexes to match.
            flags: The regex flags to use (default: 0).
        """
        patterns = tuple(re.compile(p) if isinstance(p, str) else p for p in patterns)
        return lambda _, c: any((re.match(p, c.data, flags) for p in patterns))


callback: CallbackFilterT | Type[CallbackFilter] = CallbackFilter


class MessageStatusFilter(_BaseUpdateFilter):
    """Useful filters for message status updates. Alias: ``filters.message_status``."""

    __message_types__ = ()

    any: MessageStatusFilterT = lambda _, __: True
    """
    Filter for all message status updates (the default).
        - Same as ``filters.message_status``.
        
    >>> filters.message_status.any
    """

    sent: MessageStatusFilterT = lambda _, s: s.status == Mst.SENT
    """
    Filter for messages that have been sent.
    
    >>> filters.message_status.sent
    """

    delivered: MessageStatusFilterT = lambda _, s: s.status == Mst.DELIVERED
    """
    Filter for messages that have been delivered.
    
    >>> filters.message_status.delivered
    """

    read: MessageStatusFilterT = lambda _, s: s.status == Mst.READ
    """
    Filter for messages that have been read.
    
    >>> filters.message_status.read
    """

    failed: MessageStatusFilterT = lambda _, s: s.status == Mst.FAILED
    """
    Filter for status updates of messages that have failed to send.
    
    >>> filters.message_status.failed
    """

    @staticmethod
    def failed_with(*errors: Type[WhatsAppError] | int) -> MessageStatusFilterT:
        """
        Filter for status updates of messages that have failed to send with the given error/s.

        Args:
            *errors: The exceptions from :mod:`pywa.errors` or error codes to match.

        >>> message_status.failed_with(ReEngagementMessage)
        >>> message_status.failed_with(131051)
        """
        error_codes = tuple(c for c in errors if isinstance(c, int))
        exceptions = tuple(e for e in errors if e not in error_codes and issubclass(e, WhatsAppError))
        return lambda _, s: s.status == Mst.FAILED and (
            any((isinstance(s.error, e) for e in exceptions)) or s.error.error_code in error_codes
        )


message_status: MessageStatusFilterT | Type[MessageStatusFilter] = MessageStatusFilter


class TemplateStatusFilter(_BaseUpdateFilter):
    """Useful filters for template status updates. Alias: ``filters.template_status``."""

    __message_types__ = ()

    any: TemplateStatusFilterT = lambda _, __: True
    """
    Filter for all template status updates (the default).
        - Same as ``filters.template_status``.
        
    >>> filters.template_status.any
    """

    template_name: lambda name: TemplateStatusFilterT = lambda name: lambda _, s: s.template_name == name
    """
    Filter for template status updates that are for the given template name.
    
    >>> template_status.template_name("my_template")
    """

    @staticmethod
    def on_event(*events: Ts.TemplateEvent) -> TemplateStatusFilterT:
        """
        Filter for template status updates that are for the given event/s.

        Args:
            *events: The template events to filter for.

        >>> template_status.on_event(Ts.TemplateEvent.APPROVED)
        """
        return lambda _, s: s.event in events

    @staticmethod
    def on_rejection_reason(*reasons: Ts.TemplateRejectionReason) -> TemplateStatusFilterT:
        """
        Filter for template status updates that are for the given reason/s.

        Args:
            *reasons: The template reasons to filter for.

        >>> template_status.on_rejection_reason(Ts.TemplateRejectionReason.INCORRECT_CATEGORY)
        """
        return lambda _, s: s.reason in reasons


template_status: TemplateStatusFilterT | Type[TemplateStatusFilter] = TemplateStatusFilter
