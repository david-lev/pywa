from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from .others import _FromDict

if TYPE_CHECKING:
    from pywa.client import WhatsApp


@dataclass(frozen=True, slots=True)
class MediaBase(_FromDict):
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    sha256: str
    mime_type: str

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return self._client.get_media_url(media_id=self.id).url

    def download(
            self,
            path: str | None = None,
            filename: str | None = None,
            in_memory: bool = False,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.
            - Same as ``WhatsApp.download_media(media_url=WhatsApp.get_media_url(media_id))``

        >>> message.image.download()

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(
            url=self.get_media_url(),
            path=path,
            filename=filename,
            in_memory=in_memory
        )


@dataclass(frozen=True, slots=True)
class Image(MediaBase):
    """
    Represents an image.

    Attributes:
        id: The ID of the image.
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """


@dataclass(frozen=True, slots=True)
class Video(MediaBase):
    """
    Represents a video.

    Attributes:
        id: The ID of the video.
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """


@dataclass(frozen=True, slots=True)
class Sticker(MediaBase):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the sticker.
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """
    animated: bool


@dataclass(frozen=True, slots=True)
class Document(MediaBase):
    """
    Represents a document.

    Attributes:
        id: The ID of the document.
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """
    filename: str | None = None


@dataclass(frozen=True, slots=True)
class Audio(MediaBase):
    """
    Represents an audio.

    Attributes:
        id: The ID of the audio.
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """
    voice: bool


@dataclass(frozen=True, slots=True)
class MediaUrlResponse(_FromDict):
    """
    Represents a media response.

    Attributes:
        id: The ID of the media.
        url: The URL of the media (valid for 5 minutes).
        mime_type: The MIME type of the media.
        sha256: The SHA256 hash of the media.
        file_size: The size of the media in bytes.
    """
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    url: str
    mime_type: str
    sha256: str
    file_size: int

    def download(
            self,
            filepath: str | None = None,
            filename: str | None = None,
            in_memory: bool = False,
    ) -> bytes | str:
        """
        Download a media file from WhatsApp servers.

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(url=self.url, path=filepath, filename=filename, in_memory=in_memory)
