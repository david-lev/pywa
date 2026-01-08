"""This module contains the types related to media."""

from __future__ import annotations

__all__ = [
    "Media",
    "Image",
    "Video",
    "Sticker",
    "Document",
    "Audio",
    "MediaURL",
    "UploadedBy",
]

import dataclasses
import datetime
import pathlib
from typing import TYPE_CHECKING, AsyncGenerator

from pywa.types.media import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.media import (
    URL_EXPIRATION_MINUTES,
)
from pywa.types.media import (
    Audio as _Audio,
)
from pywa.types.media import (
    Document as _Document,
)
from pywa.types.media import (
    Image as _Image,
)
from pywa.types.media import (
    Media as _Media,
)  # noqa MUST BE IMPORTED FIRST
from pywa.types.media import (
    MediaURL as _MediaURL,
)
from pywa.types.media import (
    Sticker as _Sticker,
)
from pywa.types.media import (
    Video as _Video,
)
from pywa.types.others import SuccessResult

from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp


class _MediaActionsAsync:
    _client: WhatsApp
    id: str

    async def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        if getattr(self, "url", None):
            if (
                datetime.datetime.now(datetime.timezone.utc) - self.uploaded_at
            ) < datetime.timedelta(minutes=URL_EXPIRATION_MINUTES):
                return self.url
        return (await self._client.get_media_url(media_id=self.id)).url

    async def download(
        self,
        *,
        path: str | pathlib.Path | None = None,
        filename: str | None = None,
        in_memory: None = None,
        chunk_size: int | None = None,
        **httpx_kwargs,
    ) -> pathlib.Path:
        """
        Download a media file from WhatsApp servers.

        - Same as :func:`~pywa.client.WhatsApp.download_media` with ``media_url=media.get_media_url()``

        >>> from pywa_async import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... async def on_message(_: WhatsApp, msg: types.Message):
        ...     await msg.image.download(path=pathlib.Path('/path/to/save'), filename='my_image.jpg')

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file to save (if not provided, it will be extracted from the ``Content-Disposition`` header or a SHA256 hash of the URL will be used).
            chunk_size: The size (in bytes) of each chunk to read when downloading the media (default: ``64KB``).
            in_memory: Deprecated: Use :py:func:`~pywa.client.WhatsApp.get_media_bytes` or :py:func:`~pywa.client.WhatsApp.stream_media` instead. If True, the file will be returned as bytes instead of being saved to disk.
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file.
        """
        return await self._client.download_media(
            url=await self.get_media_url(),
            path=path,
            filename=filename,
            in_memory=in_memory,
            chunk_size=chunk_size,
            **httpx_kwargs,
        )

    async def get_bytes(self, **httpx_kwargs) -> bytes:
        """
        Get the media file as bytes.

        - Same as :func:`~pywa.client.WhatsApp.get_media_bytes` with ``media_url=media.get_media_url()``

        >>> from pywa_async import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... async def on_message(_: WhatsApp, msg: types.Message):
        ...     doc_bytes = await msg.document.get_bytes()

        Args:
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The media file as bytes.
        """
        return await self._client.get_media_bytes(
            url=await self.get_media_url(),
            **httpx_kwargs,
        )

    async def stream(
        self, chunk_size: int | None = None, **httpx_kwargs
    ) -> AsyncGenerator[bytes]:
        """
        Stream the media file as bytes.

        - Same as :func:`~pywa.client.WhatsApp.stream_media` with ``media_url=media.get_media_url()``

        >>> from pywa_async import WhatsApp, types, filters

        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... async def on_message(_: WhatsApp, msg: types.Message):
        ...     async with httpx.AsyncClient() as client:
        ...        await client.post('http://example.com/upload', content=msg.document.stream())

        Args:
            chunk_size: The size (in bytes) of each chunk to read (default: ``64KB``).
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            An iterator that yields chunks of the media file as bytes.
        """
        return self._client.stream_media(
            url=await self.get_media_url(),
            chunk_size=chunk_size,
            **httpx_kwargs,
        )

    async def delete(
        self, *, phone_id: str | int | None = utils.MISSING
    ) -> SuccessResult:
        """
        Deletes the media from WhatsApp servers.

        Args:
            phone_id: The phone ID to delete the media from (optional, If included, the operation will only be processed if the ID matches the ID of the business phone number that the media was uploaded on. pass None to use the client's phone ID).
        """
        return await self._client.delete_media(media_id=self.id, phone_id=phone_id)

    async def reupload(
        self,
        *,
        to_phone_id: str | int | None = None,
        override_filename: str | None = None,
    ) -> Media:
        """
        Reuploads the media to WhatsApp servers.

        - Useful for re-sending media from another business phone number or if you want to use the media more than 30 days after it was uploaded.

        Args:
            to_phone_id: The phone ID to upload the media to (if not provided, the media owner's phone ID will be used).
            override_filename: The filename to use for the re-uploaded media (if not provided, the original filename will be used if available).
        """
        return await self._client.upload_media(
            media=self.id
            if (
                not getattr(self, "url", None)
                or (datetime.datetime.now(datetime.timezone.utc) - self.uploaded_at)
                > datetime.timedelta(minutes=URL_EXPIRATION_MINUTES)
            )
            else self.url,
            phone_id=to_phone_id or self.uploaded_to,
            filename=override_filename,
        )


class Media(_MediaActionsAsync, _Media):
    """
    Base class for all media types (async)

    Attributes:
        id: The ID of the media.
        filename: The filename of the media.
        uploaded_by: Who uploaded the media (business or user).
        uploaded_at: The timestamp when the media was uploaded (in UTC).
        uploaded_to: The phone ID the media was uploaded to.
    """

    def __enter__(self):
        raise RuntimeError(
            "Use 'async with' instead of 'with' for async context managers."
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.delete()


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Image(Media, _Image):
    """
    Represents an received image.

    Attributes:
        id: The ID of the file (can be used to download or re-send the image).
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Video(Media, _Video):
    """
    Represents a video.

    Attributes:
        id: The ID of the file (can be used to download or re-send the video).
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Sticker(Media, _Sticker):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the file (can be used to download or re-send the sticker).
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Document(Media, _Document):
    """
    Represents a document.

    Attributes:
        id: The ID of the file (can be used to download or re-send the document).
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Audio(Media, _Audio):
    """
    Represents an audio.

    Attributes:
        id: The ID of the file (can be used to download or re-send the audio).
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """


@dataclasses.dataclass(frozen=True, slots=True)
class MediaURL(_MediaActionsAsync, _MediaURL):
    """
    Represents a media response.

    - The URL is valid for 5 minutes.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """

    _client: WhatsApp

    async def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        if not self.is_expired:
            return self.url
        return (await self._client.get_media_url(media_id=self.id)).url

    async def reupload(
        self,
        *,
        to_phone_id: str | int | None = None,
        override_filename: str | None = None,
    ) -> Media:
        """
        Reuploads the media to WhatsApp servers.

        - Useful for re-sending media from another business phone number or if you want to use the media more than 30 days after it was uploaded.
        - If the media URL is expired, it will use the media ID to reupload (Will make an extra request to get a new URL).

        Args:
            to_phone_id: The phone ID to upload the media to (if not provided, the client's phone ID will be used).
            override_filename: The filename to use for the re-uploaded media (if not provided, the original filename will be used if available).
        """
        return await self._client.upload_media(
            media=self.id if self.is_expired else self.url,
            phone_id=to_phone_id,
            filename=override_filename,
        )

    async def regenerate_url(self) -> MediaURL:
        """
        Regenerates the media URL.

        - The new URL will be valid for 5 minutes.

        Returns:
            The new MediaURL object.
        """
        return await self._client.get_media_url(media_id=self.id)
