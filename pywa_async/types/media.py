"""This module contains the types related to media."""

from __future__ import annotations

from pywa.types.media import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.media import BaseMedia  # noqa MUST BE IMPORTED FIRST

import abc
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pywa_async.client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class BaseMedia(BaseMedia, abc.ABC):
    """Base class for all media types."""

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)

    async def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return (await self._client.get_media_url(media_id=self.id)).url

    async def download(
        self,
        path: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.
            - Same as :func:`~pywa.client.WhatsApp.download_media` with ``media_url=media.get_media_url()``

        >>> await message.image.download()

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to requests.get.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return await self._client.download_media(
            url=await self.get_media_url(),
            path=path,
            filename=filename,
            in_memory=in_memory,
            **kwargs,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Image(BaseMedia):
    """
    Represents an received image.

    Attributes:
        id: The ID of the file (can be used to download or re-send the image).
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """

    id: str
    sha256: str
    mime_type: str


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Video(BaseMedia):
    """
    Represents a video.

    Attributes:
        id: The ID of the file (can be used to download or re-send the video).
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """

    id: str
    sha256: str
    mime_type: str


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Sticker(BaseMedia):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the file (can be used to download or re-send the sticker).
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """

    id: str
    sha256: str
    mime_type: str
    animated: bool


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Document(BaseMedia):
    """
    Represents a document.

    Attributes:
        id: The ID of the file (can be used to download or re-send the document).
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """

    id: str
    sha256: str
    mime_type: str
    filename: str | None = None


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Audio(BaseMedia):
    """
    Represents an audio.

    Attributes:
        id: The ID of the file (can be used to download or re-send the audio).
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """

    id: str
    sha256: str
    mime_type: str
    voice: bool


@dataclasses.dataclass(frozen=True, slots=True)
class MediaUrlResponse(MediaUrlResponse):
    """
    Represents a media response.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """

    async def download(
        self,
        filepath: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to requests.get.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return await self._client.download_media(
            url=self.url,
            path=filepath,
            filename=filename,
            in_memory=in_memory,
            **kwargs,
        )