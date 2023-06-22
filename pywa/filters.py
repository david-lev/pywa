"""Usefully filters to use in your handlers."""
from __future__ import annotations

import re
from typing import Callable, TYPE_CHECKING, Iterable
from pywa import utils
from pywa.types import MessageType as Mt, Message as Msg, MessageStatus as Ms, MessageStatusType as Mst, \
    CallbackButton, CallbackSelection

if TYPE_CHECKING:
    from pywa import WhatsApp as Wa

__all__ = (
    "TextFilter",
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
)

_ONLY_NUMS_RE = re.compile(r"\D")


class TextFilter:
    """Useful filters for text messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.TEXT
    """Filter for all text messages."""

    @staticmethod
    def equals(*matches: str) -> Callable[[Wa, Msg], bool]:
        """Filter for text messages that equal the given text/s."""
        return lambda wa, m: m.type == Mt.TEXT and any((t == m.text for t in matches))

    @staticmethod
    def contains(*matches: str) -> Callable[[Wa, Msg], bool]:
        """Filter for text messages that contain the given text/s."""
        return lambda wa, m: m.type == Mt.TEXT and any((t in m.text for t in matches))

    @staticmethod
    def startswith(*matches: str) -> Callable[[Wa, Msg], bool]:
        """Filter for text messages that start with the given text/s."""
        return lambda wa, m: m.type == Mt.TEXT and any((m.text.startswith(t) for t in matches))

    @staticmethod
    def endswith(*matches: str) -> Callable[[Wa, Msg], bool]:
        """Filter for text messages that end with the given text/s."""
        return lambda wa, m: m.type == Mt.TEXT and any((m.text.endswith(t) for t in matches))

    @staticmethod
    def regex(*patterns: str | re.Pattern, flags: int = 0) -> Callable[[Wa, Msg], bool]:
        """
        Filter for text messages that match the given regex/regexes.
            * It's recommended to pass compiled regexes to save time (``re.compile(your_pattern)``)
        """
        return lambda wa, m: m.type == Mt.TEXT and any(re.match(p, m.text, flags) for p in patterns)

    @staticmethod
    def length(*lengths: tuple[int, int]) -> Callable[[Wa, Msg], bool]:
        """
        Filter for text messages that have a length between the given range/s.

        Args:
            lengths: The length range/s to filter for (e.g. (1, 10), (50, 100)).
        """
        return lambda wa, m: m.type == Mt.TEXT and any((i[0] <= len(m.text) <= i[1] for i in lengths))

    @staticmethod
    def command(*cmds: str, prefixes: str | Iterable[str] = "!") -> Callable[[Wa, Msg], bool]:
        """
        Filter for text messages that are commands.

        Args:
            cmds: The command/s to filter for (e.g. "start", "hello").
            prefixes: The prefix/s to filter for (default: "!", i.e. "!start").
        """
        return lambda wa, m: m.type == Mt.TEXT and any(m.text[0] in prefixes and m.text[1:].startswith(c) for c in cmds)


class ImageFilter:
    """Useful filters for image messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.IMAGE
    """Filter for all image messages."""

    @staticmethod
    def has_caption(wa: Wa, m: Msg) -> bool:
        """Filter for image messages that have a caption."""
        return m.type == Mt.IMAGE and m.image.caption is not None

    @staticmethod
    def mimetype(*mime_types: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for image messages that have the given mime type/s.
        See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
        """
        return lambda wa, m: m.type == Mt.IMAGE and any((t == m.image.mime_type for t in mime_types))


class VideoFilter:
    """Useful filters for video messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.VIDEO
    """Filter for all video messages."""

    @staticmethod
    def mimetype(*mime_types: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for video messages that have the given mime type/s.
        See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
        """
        return lambda wa, m: m.type == Mt.VIDEO and any((t == m.video.mime_type for t in mime_types))


class AudioFilter:
    """Useful filters for audio messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.AUDIO
    """Filter for all audio messages."""

    VOICE: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.AUDIO and m.audio.voice
    """Filter for audio messages that are voice notes."""

    AUDIO: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.AUDIO and not m.audio.voice
    """Filter for audio messages that are audio files."""

    @staticmethod
    def mimetype(*mime_types: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for audio messages that have the given mime type/s.
        See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
        """
        return lambda wa, m: m.type == Mt.AUDIO and any((t == m.audio.mime_type for t in mime_types))


class DocumentFilter:
    """Useful filters for document messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.DOCUMENT
    """Filter for all document messages."""

    @staticmethod
    def mimetype(*mime_types: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for document messages that have the given mime type/s.
        See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
        """
        return lambda wa, m: m.type == Mt.DOCUMENT and any((t == m.document.mime_type for t in mime_types))


class StickerFilter:
    """Useful filters for sticker messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.STICKER
    """Filter for all sticker messages."""

    ANIMATED: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.STICKER and m.sticker.animated
    """Filter for animated sticker messages."""

    STATIC: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.STICKER and not m.sticker.animated


class LocationFilter:
    """Useful filters for location messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.LOCATION
    """Filter for all location messages."""

    @staticmethod
    def in_radius(lat: float, lon: float, radius: float | int) -> Callable[[Wa, Msg], bool]:
        """
        Filter for location messages that are in a given radius.

        >>> LocationFilter.in_radius(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

        Args:
            lat: Latitude of the center of the radius.
            lon: Longitude of the center of the radius.
            radius: Radius in kilometers.
        """

        def _in_radius(_: Wa, msg: Msg) -> bool:
            return msg.type == Mt.LOCATION and \
                utils.get_distance(
                    lat1=lat, lon1=lon, lat2=msg.location.latitude, lon2=msg.location.longitude
                ) <= radius

        return _in_radius


class ReactionFilter:
    """Useful filters for reaction messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.REACTION
    """Filter for all reaction messages."""

    @staticmethod
    def emoji(*emojis: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for custom reaction messages. pass emojis as strings.
        """
        return lambda wa, m: m.type == Mt.REACTION and m.reaction.emoji in emojis


class ContactsFilter:
    """Useful filters for contact messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.CONTACTS
    """Filter for all contacts messages."""

    HAS_WA: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.CONTACTS and (
        any((p.wa_id for p in (phone for contact in m.contacts for phone in contact.phones)))
    )
    """Filter for contacts messages that have a WhatsApp account."""

    @staticmethod
    def count(min_count: int, max_count: int) -> Callable[[Wa, Msg], bool]:
        """Filter for contacts messages that have a number of contacts between min_count and max_count."""
        return lambda wa, m: m.type == Mt.CONTACTS and min_count <= len(m.contacts) <= max_count

    @staticmethod
    def phone(*phones: str) -> Callable[[Wa, Msg], bool]:
        """
        Filter for contacts messages that have the given phone number/s.
            * Pass only the numbers, without plus sign, spaces, etc.
        """
        return lambda wa, m: m.type == Mt.CONTACTS and (
            any((re.sub(_ONLY_NUMS_RE, "", p.phone) in phones for contact in m.contacts for p in contact.phones))
        )


class UnsupportedMsgFilter:
    """Useful filters for unsupported messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, m: m.type == Mt.UNSUPPORTED
    """Filter for all unsupported messages."""


class CallbackFilter:
    """Useful filters for callback queries."""

    @staticmethod
    def data_equals(*matches: str) -> Callable[[Wa, CallbackButton | CallbackSelection], bool]:
        """Filter for callbacks their data equals the given string/s."""
        return lambda wa, c: any((c.data == m for m in matches))

    @staticmethod
    def data_starts_with(*matches: str) -> Callable[[Wa, CallbackButton | CallbackSelection], bool]:
        """Filter for callbacks their data starts with the given string/s."""
        return lambda wa, c: any((c.data.startswith(m) for m in matches))

    @staticmethod
    def data_ends_with(*matches: str) -> Callable[[Wa, CallbackButton | CallbackSelection], bool]:
        """Filter for callbacks their data ends with the given string/s."""
        return lambda wa, c: any((c.data.endswith(m) for m in matches))

    @staticmethod
    def data_contains(*matches: str) -> Callable[[Wa, CallbackButton | CallbackSelection], bool]:
        """Filter for callbacks their data contains the given string/s."""
        return lambda wa, c: any((m in c.data for m in matches))

    @staticmethod
    def data_regex(*patterns: str | re.Pattern) -> Callable[[Wa, CallbackButton | CallbackSelection], bool]:
        """
        Filter for callbacks their data matches the given regex/regexes.
            * It's recommended to pass compiled regexes to save time (``re.compile(your_pattern)``)
        """
        return lambda wa, c: any((re.match(p, c.data) for p in patterns))


class MessageStatusFilter:
    """Useful filters for message status updates."""

    SENT: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.SENT
    """Filter for messages that have been sent."""

    DELIVERED: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.DELIVERED
    """Filter for messages that have been delivered."""

    READ: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.READ
    """Filter for messages that have been read."""
