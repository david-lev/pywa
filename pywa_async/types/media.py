"""This module contains the types related to media."""

from __future__ import annotations

__all__ = [
    "Image",
    "Video",
    "Sticker",
    "Document",
    "Audio",
    "MediaUrlResponse",
]

from pywa.types.others import SuccessResult
from .. import utils
from pywa.types.media import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.media import (
    Image as _Image,
    Video as _Video,
    Sticker as _Sticker,
    Document as _Document,
    Audio as _Audio,
    MediaUrlResponse as _MediaUrlResponse,
)  # noqa MUST BE IMPORTED FIRST

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import WhatsApp


class Media:
    """Base class for all media types."""

    def __init__(self, _client: WhatsApp, id: str):
        self._client = _client
        self.id = id

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

        >>> message.image.download()

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return await self._client.download_media(
            url=(await self.get_media_url())
            if not hasattr(self, "url")
            else self.url,  # MediaUrlResponse
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


class BaseUserMedia(Media):
    """Base class for all media types."""

    @classmethod
    def from_flow_completion(
        cls, client: WhatsApp, media: dict[str, str]
    ) -> BaseUserMedia:
        """
        Create a media object from the media dict returned by the flow completion.

        - You can use the shortcut :meth:`~pywa_async.types.FlowCompletion.get_media`

        Example:
            >>> from pywa_async import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_completion
            ... async def on_flow_completion(_: WhatsApp, flow: types.FlowCompletion):
            ...     img = types.Image.from_flow_completion(client=wa, media=flow.response['media'])
            ...     await img.download()

        Args:
            client: The WhatsApp client.
            media: The media dict returned by the flow completion.

        Returns:
            The media object (Image, Video, Sticker, Document, Audio).
        """
        # noinspection PyUnresolvedReferences
        return cls.from_dict(media, _client=client)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Image(BaseUserMedia, _Image):
    """
    Represents an received image.

    Attributes:
        id: The ID of the file (can be used to download or re-send the image).
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Video(BaseUserMedia, _Video):
    """
    Represents a video.

    Attributes:
        id: The ID of the file (can be used to download or re-send the video).
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Sticker(BaseUserMedia, _Sticker):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the file (can be used to download or re-send the sticker).
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Document(BaseUserMedia, _Document):
    """
    Represents a document.

    Attributes:
        id: The ID of the file (can be used to download or re-send the document).
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Audio(BaseUserMedia, _Audio):
    """
    Represents an audio.

    Attributes:
        id: The ID of the file (can be used to download or re-send the audio).
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """


@dataclasses.dataclass(frozen=True, slots=True)
class MediaUrlResponse(Media, _MediaUrlResponse):
    """
    Represents a media response.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """
