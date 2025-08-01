"""This module contains the types related to media."""

from __future__ import annotations


__all__ = [
    "Media",
    "Image",
    "Video",
    "Sticker",
    "Document",
    "Audio",
    "MediaUrlResponse",
]

import dataclasses
import mimetypes
from typing import TYPE_CHECKING

from .others import SuccessResult
from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True)
class Media:
    """Base class for all media types."""

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return self._client.get_media_url(media_id=self.id).url

    def download(
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
        return self._client.download_media(
            url=self.get_media_url()
            if not hasattr(self, "url")
            else self.url,  # MediaUrlResponse
            path=path,
            filename=filename,
            in_memory=in_memory,
            **kwargs,
        )

    def delete(self, *, phone_id: str | int | None = utils.MISSING) -> SuccessResult:
        """
        Deletes the media from WhatsApp servers.

        Args:
            phone_id: The phone ID to delete the media from (optional, If included, the operation will only be processed if the ID matches the ID of the business phone number that the media was uploaded on. pass None to use the client's phone ID).
        """
        return self._client.delete_media(media_id=self.id, phone_id=phone_id)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class BaseUserMedia(Media, utils.FromDict):
    """Base class for all media types."""

    sha256: str
    mime_type: str

    @property
    def extension(self) -> str | None:
        """Gets the extension of the media (with dot.)"""
        clean_mimetype = self.mime_type.split(";")[0].strip()
        return mimetypes.guess_extension(clean_mimetype)

    @classmethod
    def from_flow_completion(
        cls, client: WhatsApp, media: dict[str, str]
    ) -> BaseUserMedia:
        """
        Create a media object from the media dict returned by the flow completion.

        - You can use the shortcut :meth:`~pywa.types.FlowCompletion.get_media`

        Example:
            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_completion
            ... def on_flow_completion(_: WhatsApp, flow: types.FlowCompletion):
            ...     img = types.Image.from_flow_completion(client=wa, media=flow.response['media'])
            ...     img.download()

        Args:
            client: The WhatsApp client.
            media: The media dict returned by the flow completion.

        Returns:
            The media object (Image, Video, Sticker, Document, Audio).
        """
        return cls.from_dict(media, _client=client)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Image(BaseUserMedia):
    """
    Represents an received image.

    Attributes:
        id: The ID of the file (can be used to download or re-send the image).
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Video(BaseUserMedia):
    """
    Represents a video.

    Attributes:
        id: The ID of the file (can be used to download or re-send the video).
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Sticker(BaseUserMedia):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the file (can be used to download or re-send the sticker).
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """

    animated: bool


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Document(BaseUserMedia):
    """
    Represents a document.

    Attributes:
        id: The ID of the file (can be used to download or re-send the document).
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """

    filename: str | None = None


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Audio(BaseUserMedia):
    """
    Represents an audio.

    Attributes:
        id: The ID of the file (can be used to download or re-send the audio).
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """

    voice: bool


@dataclasses.dataclass(frozen=True, slots=True)
class MediaUrlResponse(Media, utils.FromDict):
    """
    Represents a media response.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """

    url: str
    file_size: int
    mime_type: str
    sha256: str
