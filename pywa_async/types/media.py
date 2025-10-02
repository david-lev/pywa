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

import datetime
import pathlib

from pywa.types.others import SuccessResult
from .. import utils
from pywa.types.media import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.media import (
    Image as _Image,
    Video as _Video,
    Sticker as _Sticker,
    Document as _Document,
    Audio as _Audio,
    MediaURL as _MediaURL,
)  # noqa MUST BE IMPORTED FIRST

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import WhatsApp


class Media:
    """
    Base class for all media types.

    Attributes:
        id: The ID of the media.
        uploaded_by: Who uploaded the media (business or user).
        uploaded_at: The timestamp when the media was uploaded (in UTC).
        uploaded_to: The phone ID the media was uploaded to.
    """

    id: str
    uploaded_by: UploadedBy
    uploaded_at: datetime.datetime
    uploaded_to: str

    def __init__(
        self,
        _client: WhatsApp,
        _id: str,
        uploaded_to: str,
    ):
        self._client = _client
        self.id = _id
        self.uploaded_to = uploaded_to
        self.uploaded_at = datetime.datetime.now(datetime.timezone.utc)
        self.uploaded_by = UploadedBy.BUSINESS

    def __repr__(self) -> str:
        return f"MediaAsync(id={self.id!r}, uploaded_by={self.uploaded_by!r}, uploaded_at={self.uploaded_at!r}, uploaded_to={self.uploaded_to!r})"

    async def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return (await self._client.get_media_url(media_id=self.id)).url

    async def download(
        self,
        *,
        path: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> pathlib.Path | bytes:
        """
        Download a media file from WhatsApp servers.

        - Same as :func:`~pywa.client.WhatsApp.download_media` with ``media_url=media.get_media_url()``

        >>> from pywa_async import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... async def on_message(_: WhatsApp, msg: types.Message):
        ...     await msg.image.download(...)

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to ``httpx.get(...)``.

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
            to_phone_id: The phone ID to upload the media to (if not provided, the client's phone ID will be used).
            override_filename: The filename to use for the re-uploaded media (if not provided, the original filename will be used if available).
        """
        return await self._client.upload_media(
            media=self, phone_id=to_phone_id, filename=override_filename
        )


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
class MediaURL(_MediaURL):
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

    async def download(
        self,
        *,
        path: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> pathlib.Path | bytes:
        """
        Download a media file from WhatsApp servers.

        - Same as :func:`~pywa.client.WhatsApp.download_media` with ``media_url=media.url``

        >>> from pywa_async import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... async def on_message(wa: WhatsApp, msg: types.Message):
        ...    url = await wa.get_media_url(media_id=msg.image.id)
        ...    await url.download(...)
        ...    # TIP: You can use msg.download_media() or msg.image.download() as a shortcut

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return await self._client.download_media(
            url=self.url,
            path=path,
            filename=filename,
            in_memory=in_memory,
            **kwargs,
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
