"""Usefully filters to use in your handlers."""
from __future__ import annotations

import re
from typing import Callable, TYPE_CHECKING, Iterable
from pywa.types import MessageType as Mt, Message as Msg, MessageStatus as Ms, \
    MessageStatusType as Mst, CallbackButton, CallbackSelection
from pywa import utils

if TYPE_CHECKING:
    from pywa import WhatsApp as Wa


class TextFilter:
    """Useful filters for text messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.TEXT
    """Filter for all text messages."""

    EQUALS: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and text == data.text or
            isinstance(text, Iterable) and
            any((t == data.text for t in text)))
    """Filter for text messages that equal the given text/s."""

    CONTAINS: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and text in data.text or
            isinstance(text, Iterable) and
            any((t in data.text for t in text)))
    """Filter for text messages that contain the given text/s."""

    STARTS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and data.text.startswith(text) or
            isinstance(text, Iterable) and
            any((data.text.startswith(t) for t in text)))
    """Filter for text messages that start with the given text/s."""

    ENDS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and data.text.endswith(text) or
            isinstance(text, Iterable) and
            any((data.text.endswith(t) for t in text)))
    """Filter for text messages that end with the given text/s."""

    REGEX: Callable[[str | Iterable[str] | re.Pattern | Iterable[re.Pattern]], Callable[[Wa, Msg], bool]] \
        = lambda reg: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(reg, (str, re.Pattern)) and re.match(reg, data.text) or
            isinstance(reg, Iterable) and
            any((re.match(t, data.text) for t in reg)))
    """Filter for text messages that match the given regex/regexes."""

    LEN_BETWEEN: Callable[[tuple[int, int] | Iterable[tuple[int, int]]], Callable[[Wa, Msg], bool]] \
        = lambda length: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(length, tuple) and length[0] <= len(data.text) <= length[1] or
            isinstance(length, Iterable) and
            any((l[0] <= len(data.text) <= l[1] for l in length)))
    """Filter for text messages that have a length between the given range/s."""

    @staticmethod
    def COMMAND(cmd: str | Iterable[str], prefix: str = "/") -> Callable[[Wa, Msg], bool]:
        """
        Filter for text messages that are commands.

        Args:
            cmd: The command/s to filter for.
            prefix: The prefix to filter for (default: "/").
        """
        return lambda wa, data: data.type == Mt.TEXT and (
                isinstance(cmd, str) and data.text.startswith(prefix + cmd) or
                isinstance(cmd, Iterable) and
                any((data.text.startswith(prefix + c) for c in cmd)))


class ImageFilter:
    """Useful filters for image messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.IMAGE
    """Filter for all image messages."""

    HAS_CAPTION: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.IMAGE and data.image.caption is not None
    """Filter for image messages that have a caption."""

    MIME_TYPE: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda mime: lambda wa, data: data.type == Mt.IMAGE and (
            isinstance(mime, str) and data.image.mime_type == mime or
            isinstance(mime, Iterable) and
            any((t == data.image.mime_type for t in mime)))
    """
    Filter for image messages that have the given mime type/s.
    See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
    """


class VideoFilter:
    """Useful filters for video messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.VIDEO
    """Filter for all video messages."""

    MIME_TYPE: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda mime: lambda wa, data: data.type == Mt.VIDEO and (
            isinstance(mime, str) and data.video.mime_type == mime or
            isinstance(mime, Iterable) and
            any((t == data.video.mime_type for t in mime)))
    """
    Filter for video messages that have the given mime type/s.
    See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
    """


class AudioFilter:
    """Useful filters for audio messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.AUDIO
    """Filter for all audio messages."""

    IS_VOICE: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.AUDIO and data.audio.voice
    """Filter for audio messages that are voice notes."""

    IS_AUDIO: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.AUDIO and not data.audio.voice
    """Filter for audio messages that are audio files."""

    MIME_TYPE: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda mime: lambda wa, data: data.type == Mt.AUDIO and (
            isinstance(mime, str) and data.audio.mime_type == mime or
            isinstance(mime, Iterable) and
            any((t == data.audio.mime_type for t in mime)))
    """
    Filter for audio messages that have the given mime type/s.
    See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
    """


class DocumentFilter:
    """Useful filters for document messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.DOCUMENT
    """Filter for all document messages."""

    MIME_TYPE: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda mime: lambda wa, data: data.type == Mt.DOCUMENT and (
            isinstance(mime, str) and data.document.mime_type == mime or
            isinstance(mime, Iterable) and
            any((t == data.document.mime_type for t in mime)))
    """
    Filter for document messages that have the given mime type/s. 
    See https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types
    """


class StickerFilter:
    """Useful filters for sticker messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.STICKER
    """Filter for all sticker messages."""

    IS_ANIMATED: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.STICKER and data.sticker.animated
    """Filter for animated sticker messages."""


class LocationFilter:
    """Useful filters for location messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.LOCATION
    """Filter for all location messages."""

    @staticmethod
    def IN_RADIUS(lat: float, lon: float, radius: float | int) -> Callable[[Wa, Msg], bool]:
        """
        Filter for location messages that are in a given radius.

        >>> LocationFilter.IN_RADIUS(lat=37.48508108998884, lon=-122.14744733542707, radius=1)

        Args:
            lat (float): Latitude of the center of the radius.
            lon (float): Longitude of the center of the radius.
            radius (float | int): Radius in kilometers.
        """

        def _in_radius(_: Wa, msg: Msg) -> bool:
            return msg.type == Mt.LOCATION and \
                utils.get_distance(
                    lat1=lat, lon1=lon, lat2=msg.location.latitude, lon2=msg.location.longitude
                ) <= radius

        return _in_radius


class ReactionFilter:
    """Useful filters for reaction messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.REACTION
    """Filter for all reaction messages."""

    EMOJI: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda reaction: lambda wa, data: data.type == Mt.REACTION and data.reaction.emoji in reaction
    """Filter for custom reaction messages. pass emojis as a list or a single string."""


class ContactsFilter:
    """Useful filters for contact messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.CONTACTS
    """Filter for all contacts messages."""

    COUNT_BETWEEN: Callable[[int, int], Callable[[Wa, Msg], bool]] \
        = lambda min_count, max_count: lambda wa, data: \
        data.type == Mt.CONTACTS and min_count <= len(data.contacts) <= max_count
    """Filter for contacts messages that have a number of contacts between min_count and max_count."""

    PHONE_NUMBER: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda phone_number: lambda wa, data: data.type == Mt.CONTACTS and (
            isinstance(phone_number, str) and phone_number in
            (p.phone for contact in data.contacts for p in contact.phones) or
            isinstance(phone_number, Iterable) and
            any((p.phone in phone_number for contact in data.contacts for p in contact.phones)))

    """Filter for contacts messages that have the given phone number/s."""

    HAS_WA: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.CONTACTS and \
                                                         any((p.wa_id for p in
                                                              (phone for contact in data.contacts for phone in
                                                               contact.phones)))
    """Filter for contacts messages that have a WhatsApp account."""


class UnsupportedFilter:
    """Useful filters for unsupported messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.UNSUPPORTED
    """Filter for all unsupported messages."""


class CallbackFilter:
    """Useful filters for callback queries."""

    DATA_EQUALS: Callable[[str | Iterable[str]], Callable[[Wa, CallbackButton | CallbackSelection], bool]] \
        = lambda data: lambda wa, data_: data_.data == data if isinstance(data, str) else any(
        (data_.data == d for d in data))
    """Filter for callbacks their data equals the given string/s."""

    DATA_STARTS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, CallbackButton | CallbackSelection], bool]] \
        = lambda data: lambda wa, data_: data_.data.startswith(data) if isinstance(data, str) else any(
        (data_.data.startswith(d) for d in data))
    """Filter for callbacks their data starts with the given string/s."""

    DATA_ENDS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, CallbackButton | CallbackSelection], bool]] \
        = lambda data: lambda wa, data_: data_.data.endswith(data) if isinstance(data, str) else any(
        (data_.data.endswith(d) for d in data))
    """Filter for callbacks their data ends with the given string/s."""

    DATA_CONTAINS: Callable[[str | Iterable[str]], Callable[[Wa, CallbackButton | CallbackSelection], bool]] \
        = lambda data: lambda wa, data_: data in data_.data if isinstance(data, str) else any(
        (d in data_.data for d in data))
    """Filter for callbacks their data contains the given string/s."""

    DATA_REGEX: Callable[[str | Iterable[str]], Callable[[Wa, CallbackButton | CallbackSelection], bool]] \
        = lambda regex: lambda wa, data_: re.match(regex, data_.data) if isinstance(regex, str) else any(
        (re.match(r, data_.data) for r in regex))
    """Filter for callbacks their data matches the given regex/regexes."""


class MessageStatusFilter:
    """Useful filters for message status updates."""

    SENT: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.SENT
    """Filter for messages that have been sent."""

    DELIVERED: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.DELIVERED
    """Filter for messages that have been delivered."""

    READ: Callable[[Wa, Ms], bool] = lambda wa, data: data.status == Mst.READ
    """Filter for messages that have been read."""
