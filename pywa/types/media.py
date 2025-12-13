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
import enum
import mimetypes
import pathlib
from typing import TYPE_CHECKING, Generator

from .others import SuccessResult
from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp

BUSINESS_UPLOADS_EXPIRATION_DAYS = 30
USER_UPLOADS_EXPIRATION_DAYS = 7
URL_EXPIRATION_MINUTES = 5


class UploadedBy(enum.Enum):
    """
    Enum representing who uploaded the media.

    Attributes:
        BUSINESS: The media was uploaded by the business (available for 30 days).
        USER: The media was uploaded by a user (available for 7 days).
    """

    BUSINESS = BUSINESS_UPLOADS_EXPIRATION_DAYS
    USER = USER_UPLOADS_EXPIRATION_DAYS


class _MediaActions:
    _client: WhatsApp
    id: str

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        if getattr(self, "url", None):
            if (
                datetime.datetime.now(datetime.timezone.utc) - self.uploaded_at
            ) < datetime.timedelta(minutes=URL_EXPIRATION_MINUTES):
                return self.url
        return self._client.get_media_url(media_id=self.id).url

    def download(
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

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     msg.image.download(path=pathlib.Path('/path/to/save'), filename='my_image.jpg')

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file to save (if not provided, it will be extracted from the ``Content-Disposition`` header or a SHA256 hash of the URL will be used).
            chunk_size: The size (in bytes) of each chunk to read when downloading the media (default: ``64KB``).
            in_memory: Deprecated: Use :py:func:`~pywa.client.WhatsApp.get_media_bytes` or :py:func:`~pywa.client.WhatsApp.stream_media` instead. If True, the file will be returned as bytes instead of being saved to disk.
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file.
        """
        return self._client.download_media(
            url=self.get_media_url(),
            path=path,
            filename=filename,
            in_memory=in_memory,
            chunk_size=chunk_size,
            **httpx_kwargs,
        )

    def get_bytes(self, **httpx_kwargs) -> bytes:
        """
        Get the media file as bytes.

        - Same as :func:`~pywa.client.WhatsApp.get_media_bytes` with ``media_url=media.get_media_url()``

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     doc_bytes = msg.document.get_bytes()

        Args:
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The media file as bytes.
        """
        return self._client.get_media_bytes(
            url=self.get_media_url(),
            **httpx_kwargs,
        )

    def stream(self, chunk_size: int | None = None, **httpx_kwargs) -> Generator[bytes]:
        """
        Stream the media file as bytes.

        - Same as :func:`~pywa.client.WhatsApp.stream_media` with ``media_url=media.get_media_url()``

        >>> from pywa import WhatsApp, types, filters

        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     with httpx.Client() as client:
        ...        client.post('http://example.com/upload', content=msg.document.stream())

        Args:
            chunk_size: The size (in bytes) of each chunk to read (default: ``64KB``).
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            An iterator that yields chunks of the media file as bytes.
        """
        return self._client.stream_media(
            url=self.get_media_url(),
            chunk_size=chunk_size,
            **httpx_kwargs,
        )

    def delete(self, *, phone_id: str | int | None = utils.MISSING) -> SuccessResult:
        """
        Deletes the media from WhatsApp servers.

        Args:
            phone_id: The phone ID to delete the media from (optional, If included, the operation will only be processed if the ID matches the ID of the business phone number that the media was uploaded on. pass None to use the client's phone ID).
        """
        return self._client.delete_media(media_id=self.id, phone_id=phone_id)

    def reupload(
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
        return self._client.upload_media(
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


class Media(_MediaActions):
    """
    Base class for all media types.

    Attributes:
        id: The ID of the media.
        filename: The filename of the media.
        uploaded_by: Who uploaded the media (business or user).
        uploaded_at: The timestamp when the media was uploaded (in UTC).
        uploaded_to: The phone ID the media was uploaded to.
    """

    id: str
    filename: str | None
    uploaded_by: UploadedBy
    uploaded_at: datetime.datetime
    uploaded_to: str

    def __init__(
        self,
        _client: WhatsApp,
        _id: str,
        filename: str | None,
        uploaded_to: str,
        ttl_minutes: int | None = None,
    ):
        self._client = _client
        self.id = _id
        self.filename = filename
        self.uploaded_to = uploaded_to
        self.uploaded_at = datetime.datetime.now(datetime.timezone.utc)
        self.ttl_minutes = ttl_minutes
        self.uploaded_by = UploadedBy.BUSINESS

    def __repr__(self) -> str:
        return (
            f"Media(id={self.id!r}, filename={self.filename!r}, "
            f"uploaded_by={self.uploaded_by!r}, uploaded_at={self.uploaded_at!r}, expires_at={self.expires_at!r}, "
            f"uploaded_to={self.uploaded_to!r})"
        )

    @property
    def is_expired(self) -> bool:
        """Checks if the media is expired (30 days for business uploaded media, 7 days for user uploaded media)."""
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    @property
    def expires_at(self) -> datetime.datetime:
        """Gets the expiration date of the media (30 days for business uploaded media, 7 days for user uploaded media)."""
        return self.uploaded_at + (
            datetime.timedelta(days=self.uploaded_by.value)
            if self.ttl_minutes is None
            else datetime.timedelta(minutes=self.ttl_minutes)
        )

    @property
    def days_until_expiration(self) -> int:
        """Gets the number of days until the media expires."""
        delta = self.expires_at - datetime.datetime.now(datetime.timezone.utc)
        return max(delta.days, 0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.delete()


def _get_arrived_media_dict(
    client: WhatsApp,
    data: dict,
    arrived_at: datetime.datetime | None = None,
    received_to: str | None = None,
    additional_field: str | None = None,
) -> dict:
    return dict(
        _client=client,
        id=data["id"],
        filename=data.get("filename"),
        sha256=data["sha256"],
        mime_type=data["mime_type"],
        url=data.get("url"),
        uploaded_by=UploadedBy.USER,
        uploaded_at=arrived_at or datetime.datetime.now(datetime.timezone.utc),
        uploaded_to=received_to,
        **({additional_field: data.get(additional_field)} if additional_field else {}),
    )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ArrivedMedia(Media):
    """
    Base class for all media types that can be received in a message.

    Attributes:
        id: The ID of the file (can be used to download or re-send the media later, but only for 7 days after it was uploaded by the user).
        filename: The filename of the media (only for documents or when arrived via flow completion).
        sha256: The SHA256 hash of the media.
        mime_type: The MIME type of the media.
        url: The URL of the media (may be None in webhook versions before 24.0, use :meth:`~pywa.types.ArrivedMedia.get_media_url` to get it).
        uploaded_by: Who uploaded the media (always USER for arrived media).
        uploaded_at: The timestamp when the message containing the media was received (in UTC).
        uploaded_to: The phone ID the media was received to (optional when constructing manually).
    """

    _client: WhatsApp = dataclasses.field(repr=False)
    id: str
    filename: str | None = None
    sha256: str
    mime_type: str
    url: str | None
    uploaded_by: UploadedBy
    uploaded_at: datetime.datetime
    uploaded_to: str | None = None

    @classmethod
    def from_dict(
        cls,
        client: WhatsApp,
        data: dict,
        arrived_at: datetime.datetime | None = None,
        received_to: str | None = None,
    ) -> ArrivedMedia:
        """Creates an ArrivedMedia object from a dictionary."""
        return cls(
            **_get_arrived_media_dict(
                client=client, data=data, arrived_at=arrived_at, received_to=received_to
            )
        )

    @property
    def extension(self) -> str | None:
        """Gets the extension of the media (with dot.)"""
        clean_mimetype = self.mime_type.split(";")[0].strip()
        return mimetypes.guess_extension(clean_mimetype)

    @classmethod
    def from_flow_completion(
        cls, client: WhatsApp, media: dict[str, str]
    ) -> ArrivedMedia:
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
        return cls.from_dict(client=client, data=media)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Image(ArrivedMedia):
    """
    Represents a received image.

    Attributes:
        id: The ID of the file (can be used to download or re-send the image).
        sha256: The SHA256 hash of the image.
        mime_type: The MIME type of the image.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Video(ArrivedMedia):
    """
    Represents a video.

    Attributes:
        id: The ID of the file (can be used to download or re-send the video).
        sha256: The SHA256 hash of the video.
        mime_type: The MIME type of the video.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Sticker(ArrivedMedia):
    """
    Represents a sticker.

    Attributes:
        id: The ID of the file (can be used to download or re-send the sticker).
        sha256: The SHA256 hash of the sticker.
        mime_type: The MIME type of the sticker.
        animated: Whether the sticker is animated.
    """

    animated: bool

    @classmethod
    def from_dict(
        cls,
        client: WhatsApp,
        data: dict,
        arrived_at: datetime.datetime | None = None,
        received_to: str | None = None,
    ) -> Sticker:
        return cls(
            **_get_arrived_media_dict(
                client=client,
                data=data,
                arrived_at=arrived_at,
                received_to=received_to,
                additional_field="animated",
            )
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Document(ArrivedMedia):
    """
    Represents a document.

    Attributes:
        id: The ID of the file (can be used to download or re-send the document).
        sha256: The SHA256 hash of the document.
        mime_type: The MIME type of the document.
        filename: The filename of the document (optional).
    """

    @property
    def extension(self) -> str | None:
        """Gets the extension of the document (with dot.)"""
        return pathlib.Path(self.filename or "").suffix or super().extension


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Audio(ArrivedMedia):
    """
    Represents an audio.

    Attributes:
        id: The ID of the file (can be used to download or re-send the audio).
        sha256: The SHA256 hash of the audio.
        mime_type: The MIME type of the audio.
        voice: Whether the audio is a voice message or just an audio file.
    """

    voice: bool

    @classmethod
    def from_dict(
        cls,
        client: WhatsApp,
        data: dict,
        arrived_at: datetime.datetime | None = None,
        received_to: str | None = None,
    ) -> Audio:
        return cls(
            **_get_arrived_media_dict(
                client=client,
                data=data,
                arrived_at=arrived_at,
                received_to=received_to,
                additional_field="voice",
            )
        )


@dataclasses.dataclass(frozen=True, slots=True)
class MediaURL(_MediaActions):
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

    _client: WhatsApp = dataclasses.field(repr=False)
    id: str
    url: str
    file_size: int
    mime_type: str
    sha256: str
    generated_at: datetime.datetime = dataclasses.field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict) -> MediaURL:
        return cls(
            _client=client,
            id=data["id"],
            url=data["url"],
            file_size=data["file_size"],
            mime_type=data["mime_type"],
            sha256=data["sha256"],
            generated_at=datetime.datetime.now(datetime.timezone.utc),
        )

    @property
    def expires_at(self) -> datetime.datetime:
        """Gets the expiration date of the media URL (5 minutes after creation)."""
        return self.generated_at + datetime.timedelta(minutes=URL_EXPIRATION_MINUTES)

    @property
    def is_expired(self) -> bool:
        """Checks if the media URL is expired. If expired, you need to regenerate it."""
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    @property
    def minutes_until_expiration(self) -> int:
        """Gets the number of minutes until the media URL expires."""
        return max(
            (self.expires_at - datetime.datetime.now(datetime.timezone.utc)).seconds
            // 60,
            0,
        )

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        if not self.is_expired:
            return self.url
        return self._client.get_media_url(media_id=self.id).url

    def reupload(
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
        return self._client.upload_media(
            media=self.id if self.is_expired else self.url,
            phone_id=to_phone_id,
            filename=override_filename,
        )

    def regenerate_url(self) -> MediaURL:
        """
        Regenerates the media URL.

        - The new URL will be valid for 5 minutes.

        Returns:
            The new MediaURL object.
        """
        return self._client.get_media_url(media_id=self.id)
