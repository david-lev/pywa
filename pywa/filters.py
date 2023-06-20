"""Usefully filters to use in your handlers."""
from __future__ import annotations

import re
from typing import Callable, Any, TYPE_CHECKING, Iterable

from pywa.types import MessageType as Mt, Message as Msg

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
            any([t == data.text for t in text]))
    """Filter for text messages that equal the given text/s."""

    CONTAINS: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and text in data.text or
            isinstance(text, Iterable) and
            any([t in data.text for t in text]))
    """Filter for text messages that contain the given text/s."""

    STARTS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and data.text.startswith(text) or
            isinstance(text, Iterable) and
            any([data.text.startswith(t) for t in text]))
    """Filter for text messages that start with the given text/s."""

    ENDS_WITH: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda text: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(text, str) and data.text.endswith(text) or
            isinstance(text, Iterable) and
            any([data.text.endswith(t) for t in text]))
    """Filter for text messages that end with the given text/s."""
    
    REGEX_MATCH: Callable[[str | Iterable[str] | re.Pattern | Iterable[re.Pattern]], Callable[[Wa, Msg], bool]] \
        = lambda reg: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(reg, (str, re.Pattern)) and re.match(reg, data.text) or
            isinstance(reg, Iterable) and
            any([re.match(t, data.text) for t in reg]))
    """Filter for text messages that match the given regex/regexes."""

    REGEX_SEARCH: Callable[[str | Iterable[str] | re.Pattern | Iterable[re.Pattern]], Callable[[Wa, Msg], bool]] \
        = lambda reg: lambda wa, data: data.type == Mt.TEXT and (
            isinstance(reg, (str, re.Pattern)) and re.search(reg, data.text) or
            isinstance(reg, Iterable) and
            any([re.search(t, data.text) for t in reg]))
    """Filter for text messages that match the given regex/regexes."""


class ImageFilter:
    """Useful filters for image messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.IMAGE
    """Filter for all image messages."""

    HAS_CAPTION: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.IMAGE and data.image.caption is not None
    """Filter for image messages that have a caption."""


class VideoFilter:
    """Useful filters for video messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.VIDEO
    """Filter for all video messages."""


class AudioFilter:
    """Useful filters for audio messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.AUDIO
    """Filter for all audio messages."""

    IS_VOICE: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.AUDIO and data.audio.voice
    """Filter for audio messages that are voice notes."""


class DocumentFilter:
    """Useful filters for document messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.DOCUMENT
    """Filter for all document messages."""


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

    IN_RADIUS: Callable[[float, float, float | int], Callable[[Wa, Msg], bool]] \
        = lambda lat, lon, radius: lambda wa, data: data.type == Mt.LOCATION and (
            (data.location.latitude - lat) ** 2 + (data.location.longitude - lon) ** 2 <= radius ** 2)
    """Filter for location messages that are in the given radius."""


class ReactionFilter:
    """Useful filters for reaction messages."""

    ANY: Callable[[Wa, Msg], bool] = lambda wa, data: data.type == Mt.REACTION
    """Filter for all reaction messages."""

    CUSTOM: Callable[[str | Iterable[str]], Callable[[Wa, Msg], bool]] \
        = lambda reaction: lambda wa, data: data.type == Mt.REACTION and data.reaction.emoji in reaction
    """Filter for custom reaction messages. pass emojis as a list or a single string."""

