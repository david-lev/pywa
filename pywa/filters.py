"""Usefully filters to use in your handlers."""
from __future__ import annotations

__all__ = (
    "all_",
    "any_",
    "not_",
    "forwarded",
    "forwarded_many_times",
    "reply",
    "from_users",
    "TextFilter",
    "MediaFilter",
    "ImageFilter",
    "VideoFilter",
    "AudioFilter",
    "DocumentFilter",
    "StickerFilter",
    "ReactionFilter",
    "UnsupportedMsgFilter",
    "LocationFilter",
    "ContactsFilter",
    "CallbackFilter",
    "MessageStatusFilter"
)

import re
from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING, Iterable, TypeVar, TypeAlias, Type
from pywa import utils
from pywa.errors import WhatsAppError, ReEngagementMessage, MessageUndeliverable
from pywa.types import MessageType as Mt, Message as Msg, MessageStatus as Ms, MessageStatusType as Mst, \
    CallbackButton, CallbackSelection
from pywa.types.base_update import BaseUpdate

if TYPE_CHECKING:
    from pywa import WhatsApp as Wa

    MessageFilterT: TypeAlias = Callable[[Wa, Msg], bool]
    CallbackFilterT: TypeAlias = Callable[[Wa, CallbackButton | CallbackSelection], bool]
    MessageStatusFilterT: TypeAlias = Callable[[Wa, Ms], bool]

T = TypeVar("T", bound=BaseUpdate)

forwarded: MessageFilterT = lambda wa, m: m.forwarded  # Filter for forwarded messages.
"""
Filter for forwarded messages.

>>> filters.forwarded
"""

forwarded_many_times: MessageFilterT = lambda wa, m: m.forwarded_many_times
"""
Filter for messages that have been forwarded many times.

>>> filters.forwarded_many_times
"""

reply: MessageFilterT = lambda wa, m: m.reply_to_message is not None
"""
Filter for messages that reply to another message.

>>> filters.reply
"""


def all_(*filters: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that pass all the given filters.

    >>> all_(TextFilter.startswith("World"), TextFilter.contains("Word"))
    """
    return lambda wa, m: all(f(wa, m) for f in filters)


def any_(*filters: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that pass any of the given filters.

    >>> any_(TextFilter.contains("Hello"), TextFilter.contains("World"))
    """
    return lambda wa, m: any(f(wa, m) for f in filters)


def not_(fil: Callable[[Wa, T], bool]) -> Callable[[Wa, T], bool]:
    """
    Filter for updates that don't pass the given filter.

    >>> not_(TextFilter.contains("Hello"))
    """
    return lambda wa, m: not fil(wa, m)


def from_users(*numbers: str) -> MessageFilterT:
    """
    Filter for messages that are sent from the given numbers.

    >>> filters.from_users("+1 555-555-5555","972123456789")
    """
    only_nums_pattern = re.compile(r"\D")
    numbers = tuple(re.sub(only_nums_pattern, "", n) for n in numbers)
    return lambda wa, m: m.from_user.wa_id in numbers


class _BaseUpdateFilter(ABC):
    """
    Base class for all filters.
    """

    @abstractmethod
    def __new__(cls) -> Callable[[Wa, T], bool]:
        ...

    @property
    @abstractmethod
    def __message_types__(self) -> tuple[Mt, ...]:
        """The message types that the filter is for."""
        ...

    @classmethod
    def _match_type(cls, m: Msg) -> bool:
        return m.type in cls.__message_types__


class MediaFilter(_BaseUpdateFilter):
    """
    Useful filters for media messages.
    """
    __message_types__ = (Mt.IMAGE, Mt.VIDEO, Mt.AUDIO, Mt.DOCUMENT, Mt.STICKER)

    def __new__(cls):
        return cls.any

    """
    Filter for all media messages.
        - Same as ``MediaFilter()``.
    
    >>> MediaFilter.any
    """
    any: MessageFilterT = lambda wa, m: m.has_media

    @classmethod
    def mimetypes(cls, *mimetypes: str) -> MessageFilterT:
        """
        Filter for media messages that match any of the given mime types.
            - See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types

        >>> ImageFilter.mimetypes("image/png", "image/jpeg")
        """
        return lambda wa, m: cls._match_type(m) and any(
            t == getattr(m, cls.__message_types__[0].value).mime_type for t in mimetypes
        )


class _MediaWithCaptionFilter(MediaFilter, ABC):
    @classmethod
    def _has_caption(cls, _: Wa, m: Msg) -> bool:
        return cls._match_type(m) and m.caption is not None

    has_caption: MessageFilterT = _has_caption
    """
    Filter for media messages that have a caption.
    
    >>> ImageFilter.has_caption
    """


class TextFilter(_BaseUpdateFilter):
    """Useful filters for text messages."""

    __message_types__ = (Mt.TEXT,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda wa, m: m.type == Mt.TEXT and not TextFilter.is_command(wa, m)
    """
    Filter for all text messages (excluding commands).
        - Same as ``TextFilter()``.
    
    >>> TextFilter.any
    """

    is_command: MessageFilterT = lambda wa, m: m.type == Mt.TEXT and m.text.startswith(("!", "/", "#"))
    """
    Filter for text messages that are commands (start with ``!``, ``/``, or ``#``).
        - Use TextFilter.command if you want to filter for specific commands or prefixes.
    
    >>> TextFilter.is_command
    """

    @staticmethod
    def matches(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that match exactly the given text/s.

        >>> TextFilter.matches("Hello","Hi")

        Args:
            matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text) in matches

    @staticmethod
    def contains(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that contain the given text/s.

        >>> TextFilter.contains("Cat","Dog",ignore_case=True)

        Args:
            matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching. (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, m: TextFilter._match_type(m) and any(
            t in (m.text.lower() if ignore_case else m.text) for t in matches
        )

    @staticmethod
    def startswith(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that start with the given text/s.

        >>> TextFilter.startswith("What", "When", ignore_case=True)

        Args:
            matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text).startswith(
            matches)

    @staticmethod
    def endswith(*matches: str, ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that end with the given text/s.

        >>> TextFilter.endswith("Bye", "See you", ignore_case=True)

        Args:
            matches: The text/s to filter for.
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, m: TextFilter._match_type(m) and (m.text.lower() if ignore_case else m.text).endswith(matches)

    @staticmethod
    def regex(*patterns: str | re.Pattern, flags: int = 0) -> MessageFilterT:
        """
        Filter for text messages that match the given regex/regexes.

        >>> TextFilter.regex(r"Hello\s+World", r"Bye\s+World", flags=re.IGNORECASE)

        Args:
            patterns: The regex/regexes to filter for.
            flags: The regex flags to use (default: ``0``).
        """
        patterns = tuple(re.compile(p, flags) if isinstance(p, str) else p for p in patterns)
        return lambda wa, m: TextFilter._match_type(m) and any(re.match(p, m.text, flags) for p in patterns)

    @staticmethod
    def length(*lengths: tuple[int, int]) -> MessageFilterT:
        """
        Filter for text messages that have a length between the given range/s.

        >>> TextFilter.length((1, 10), (50, 100))

        Args:
            lengths: The length range/s to filter for (e.g. (1, 10), (50, 100)).
        """
        return lambda wa, m: TextFilter._match_type(m) and any(i[0] <= len(m.text) <= i[1] for i in lengths)

    @staticmethod
    def command(*cmds: str, prefixes: str | Iterable[str] = "!", ignore_case: bool = False) -> MessageFilterT:
        """
        Filter for text messages that are commands.

        >>> TextFilter.command("start", "hello", prefixes=("!", "/"), ignore_case=True)

        Args:
            cmds: The command/s to filter for (e.g. "start", "hello").
            prefixes: The prefix/s to filter for (default: "!", i.e. "!start").
            ignore_case: Whether to ignore case when matching (default: ``False``).
        """
        cmds = tuple(c.lower() for c in cmds) if ignore_case else cmds
        return lambda wa, m: TextFilter._match_type(m) and (
                m.text[0] in prefixes and (m.text[1:].lower() if ignore_case else m.text[1:]).startswith(cmds)
        )


class ImageFilter(_MediaWithCaptionFilter):
    """Useful filters for image messages."""

    __message_types__ = (Mt.IMAGE,)

    any: MessageFilterT = lambda wa, m: ImageFilter._match_type(m)
    """
    Filter for all image messages.
    
    >>> ImageFilter.any
    """


class VideoFilter(_MediaWithCaptionFilter):
    """Useful filters for video messages."""

    __message_types__ = (Mt.VIDEO,)

    any: MessageFilterT = lambda wa, m: VideoFilter._match_type(m)
    """
    Filter for all video messages.
    
    >>> VideoFilter.any
    """


class DocumentFilter(_MediaWithCaptionFilter):
    """Useful filters for document messages."""

    __message_types__ = (Mt.DOCUMENT,)

    any: MessageFilterT = lambda wa, m: DocumentFilter._match_type(m)
    """
    Filter for all document messages.
    
    >>> DocumentFilter.any
    """


class AudioFilter(MediaFilter):
    """Useful filters for audio messages."""

    __message_types__ = (Mt.AUDIO,)

    any: MessageFilterT = lambda wa, m: AudioFilter._match_type(m)
    """
    Filter for all audio messages (voice notes and audio files).
    
    >>> AudioFilter.any
    """

    voice: MessageFilterT = lambda wa, m: AudioFilter._match_type(m) and m.audio.voice
    """
    Filter for audio messages that are voice notes.
    
    >>> AudioFilter.voice
    """

    audio: MessageFilterT = lambda wa, m: AudioFilter._match_type(m) and not m.audio.voice
    """
    Filter for audio messages that are audio files.
    
    >>> AudioFilter.audio
    """


class StickerFilter(MediaFilter):
    """Useful filters for sticker messages."""

    __message_types__ = (Mt.STICKER,)

    any: MessageFilterT = lambda wa, m: StickerFilter._match_type(m)
    """
    Filter for all sticker messages.
    
    >>> StickerFilter.any
    """

    animated: MessageFilterT = lambda wa, m: StickerFilter._match_type(m) and m.sticker.animated
    """
    Filter for animated sticker messages.
    
    >>> StickerFilter.animated
    """

    static: MessageFilterT = lambda wa, m: StickerFilter._match_type(m) and not m.sticker.animated
    """
    Filter for static sticker messages.
    
    >>> StickerFilter.static
    """


class LocationFilter(_BaseUpdateFilter):
    """Useful filters for location messages."""

    __message_types__ = (Mt.LOCATION,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda wa, m: LocationFilter._match_type(m)
    """
    Filter for all location messages.
        - Same as ``LocationFilter()``.
    
    >>> LocationFilter.any
    """

    @staticmethod
    def in_radius(lat: float, lon: float, radius: float | int) -> MessageFilterT:
        """
        Filter for location messages that are in a given radius.

        >>> LocationFilter.in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

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


class ReactionFilter(_BaseUpdateFilter):
    """Useful filters for reaction messages."""

    __message_types__ = (Mt.REACTION,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda wa, m: ReactionFilter._match_type(m)
    """
    Filter for all reaction updates (added or removed).
        - Same as ``ReactionFilter()``.
    
    >>> ReactionFilter.any
    """

    added: MessageFilterT = lambda wa, m: ReactionFilter._match_type(m) and m.reaction.emojis is not None
    """
    Filter for reaction messages that were added.
    
    >>> ReactionFilter.added
    """

    removed: MessageFilterT = lambda wa, m: ReactionFilter._match_type(m) and m.reaction.emojis is None
    """
    Filter for reaction messages that were removed.
    
    >>> ReactionFilter.removed
    """

    @staticmethod
    def emojis(*emojis: str) -> MessageFilterT:
        """
        Filter for custom reaction messages. pass emojis as strings.

        >>> ReactionFilter.emojis("👍","👎")
        """
        return lambda wa, m: ReactionFilter._match_type(m) and m.reaction.emojis in emojis


class ContactsFilter(_BaseUpdateFilter):
    """Useful filters for contact messages."""

    __message_types__ = (Mt.CONTACTS,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda wa, m: ContactsFilter._match_type(m)
    """
    Filter for all contacts messages.
        - Same as ``ContactsFilter()``.
    
    >>> ContactsFilter.any
    """

    has_wa: MessageFilterT = lambda wa, m: ContactsFilter._match_type(m) and (
        any((p.wa_id for p in (phone for contact in m.contacts for phone in contact.phones)))
    )
    """Filter for contacts messages that have a WhatsApp account."""

    @staticmethod
    def count(min_count: int, max_count: int) -> MessageFilterT:
        """
        Filter for contacts messages that have a number of contacts between min_count and max_count.

        >>> ContactsFilter.count(1, 1) # ensure only 1 contact
        >>> ContactsFilter.count(1, 5) # between 1 and 5 contacts
        """
        return lambda wa, m: ContactsFilter._match_type(m) and min_count <= len(m.contacts) <= max_count

    @staticmethod
    def phones(*phones: str) -> MessageFilterT:
        """
        Filter for contacts messages that have the given phone number/s.

        >>> ContactsFilter.phones("+1 555-555-5555","972123456789")
        """
        only_nums_pattern = re.compile(r"\D")
        phones = [re.sub(only_nums_pattern, "", p) for p in phones]
        return lambda wa, m: ContactsFilter._match_type(m) and (
            any(re.sub(only_nums_pattern, "", p.phones) in phones for contact in m.contacts for p in contact.phones)
        )


class UnsupportedMsgFilter(_BaseUpdateFilter):
    """Useful filters for unsupported messages."""

    __message_types__ = (Mt.UNSUPPORTED,)

    def __new__(cls):
        return cls.any

    any: MessageFilterT = lambda wa, m: m.type == Mt.UNSUPPORTED
    """
    Filter for all unsupported messages.
        - Same as ``UnsupportedMsgFilter()``.
    
    >>> UnsupportedMsgFilter.any
    """


class CallbackFilter(_BaseUpdateFilter):
    """Useful filters for callback queries."""

    __message_types__ = (Mt.INTERACTIVE,)

    def __new__(cls):
        return cls.any

    any: CallbackFilterT = lambda wa, c: True
    """
    Filter for all callback queries (the default).
        - Same as ``CallbackFilter()``.
    
    >>> CallbackFilter.any
    """

    @staticmethod
    def data_matches(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data match exactly the given string/s.

        >>> CallbackFilter.data_matches("menu")
        >>> CallbackFilter.data_matches("back","return","exit")

        Args:
            matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, c: (c.data.lower() if ignore_case else c.data) in matches

    @staticmethod
    def data_startswith(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data starts with the given string/s.

        >>> CallbackFilter.data_startswith("id:")

        Args:
            matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, c: (c.data.lower() if ignore_case else c.data).startswith(matches)

    @staticmethod
    def data_endswith(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data ends with the given string/s.

        >>> CallbackFilter.data_endswith(":true", ":false")

        Args:
            matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, c: (c.data.lower() if ignore_case else c.data).endswith(matches)

    @staticmethod
    def data_contains(*matches: str, ignore_case: bool = False) -> CallbackFilterT:
        """
        Filter for callbacks their data contains the given string/s.

        >>> CallbackFilter.data_contains("back")

        Args:
            matches: The string/s to match.
            ignore_case: Whether to ignore case when matching (default: False).
        """
        matches = tuple(m.lower() for m in matches) if ignore_case else matches
        return lambda wa, c: any((m in (c.data.lower() if ignore_case else c.data) for m in matches))

    @staticmethod
    def data_regex(*patterns: str | re.Pattern, flags: int = 0) -> CallbackFilterT:
        """
        Filter for callbacks their data matches the given regex/regexes.

        >>> CallbackFilter.data_regex(r"^\d+$")  # only digits

        Args:
            patterns: The regex/regexes to match.
            flags: The regex flags to use (default: 0).
        """
        patterns = tuple(re.compile(p) if isinstance(p, str) else p for p in patterns)
        return lambda wa, c: any((re.match(p, c.data, flags) for p in patterns))


class MessageStatusFilter(_BaseUpdateFilter):
    """Useful filters for message status updates."""

    __message_types__ = (Mt.MESSAGE_STATUS,)

    def __new__(cls):
        return cls.any

    any: MessageStatusFilterT = lambda wa, s: True
    """
    Filter for all message status updates (the default).
        - Same as ``MessageStatusFilter()``.
        
    >>> MessageStatusFilter.any
    """

    sent: MessageStatusFilterT = lambda wa, data: data.status == Mst.SENT
    """
    Filter for messages that have been sent.
    
    >>> MessageStatusFilter.sent
    """

    delivered: MessageStatusFilterT = lambda wa, data: data.status == Mst.DELIVERED
    """
    Filter for messages that have been delivered.
    
    >>> MessageStatusFilter.delivered
    """

    read: MessageStatusFilterT = lambda wa, data: data.status == Mst.READ
    """
    Filter for messages that have been read.
    
    >>> MessageStatusFilter.read
    """

    failed: MessageStatusFilterT = lambda wa, data: data.status == Mst.FAILED
    """
    Filter for status updates of messages that have failed to send.
    
    >>> MessageStatusFilter.failed
    """

    @staticmethod
    def failed_with(*errors: Type[WhatsAppError] | int) -> MessageStatusFilterT:
        """
        Filter for status updates of messages that have failed to send with the given error/s.

        Args:
            errors: The exceptions from `pywa.errors` or error codes to match.

        >>> MessageStatusFilter.failed_with(ReEngagementMessage)
        >>> MessageStatusFilter.failed_with(131051)
        """
        exceptions = tuple(e for e in errors if issubclass(e, WhatsAppError))
        error_codes = tuple(e for e in errors if isinstance(e, int))
        return lambda wa, s: (s.status == Mst.FAILED and
                              (isinstance(s.error, exceptions) or s.error.error_code in error_codes))
