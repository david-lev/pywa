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
from typing import TYPE_CHECKING

from .others import SuccessResult
from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp


class UploadedBy(enum.Enum):
    """
    Enum representing who uploaded the media.

    Attributes:
        BUSINESS: The media was uploaded by the business (available for 30 days).
        USER: The media was uploaded by a user (available for 7 days).
    """

    BUSINESS = 30
    USER = 7


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
        return f"Media(id={self.id!r}, uploaded_by={self.uploaded_by!r}, uploaded_at={self.uploaded_at!r}, uploaded_to={self.uploaded_to!r})"

    @property
    def is_expired(self) -> bool:
        """Checks if the media is expired (30 days for business uploaded media, 7 days for user uploaded media)."""
        return datetime.datetime.now(datetime.timezone.utc) > (
            self.uploaded_at + datetime.timedelta(days=self.uploaded_by.value)
        )

    @property
    def expires_at(self) -> datetime.datetime:
        """Gets the expiration date of the media."""
        return self.uploaded_at + datetime.timedelta(days=self.uploaded_by.value)

    @property
    def days_until_expiration(self) -> int:
        """Gets the number of days until the media expires."""
        delta = self.expires_at - datetime.datetime.now(datetime.timezone.utc)
        return max(delta.days, 0)

    def get_media_url(self) -> str:
        """Gets the URL of the media. (expires after 5 minutes)"""
        return self._client.get_media_url(media_id=self.id).url

    def download(
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

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     msg.image.download(...)

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(
            url=self.get_media_url(),
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
            to_phone_id: The phone ID to upload the media to (if not provided, the client's phone ID will be used).
            override_filename: The filename to use for the re-uploaded media (if not provided, the original filename will be used if available).
        """
        return self._client.upload_media(
            media=self, phone_id=to_phone_id, filename=override_filename
        )


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
        sha256=data["sha256"],
        mime_type=data["mime_type"],
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
        sha256: The SHA256 hash of the media.
        mime_type: The MIME type of the media.
        uploaded_by: Who uploaded the media (always USER for arrived media).
        uploaded_at: The timestamp when the message containing the media was received (in UTC).
        uploaded_to: The phone ID the media was received to (optional when constructing manually).
    """

    _client: WhatsApp = dataclasses.field(repr=False)
    id: str
    sha256: str
    mime_type: str
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

    filename: str | None

    @classmethod
    def from_dict(
        cls,
        client: WhatsApp,
        data: dict,
        arrived_at: datetime.datetime | None = None,
        received_to: str | None = None,
    ) -> Document:
        return cls(
            **_get_arrived_media_dict(
                client=client,
                data=data,
                arrived_at=arrived_at,
                received_to=received_to,
                additional_field="filename",
            )
        )

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
class MediaURL:
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
        return self.generated_at + datetime.timedelta(minutes=5)

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

    def download(
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

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... def on_message(wa: WhatsApp, msg: types.Message):
        ...    url = wa.get_media_url(media_id=msg.image.id)
        ...    url.download(...)
        ...    # TIP: You can use msg.download_media() or msg.image.download() as a shortcut

        Args:
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        return self._client.download_media(
            url=self.url,
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
