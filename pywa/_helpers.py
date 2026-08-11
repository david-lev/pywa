import base64
import dataclasses
import datetime
import enum
import functools
import importlib.util
import inspect
import io
import itertools
import json
import logging
import mimetypes
import os
import pathlib
import re
import threading
import types
import warnings
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Iterable,
    Iterator,
    Sequence,
)
from concurrent import futures
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    ClassVar,
    Literal,
    NamedTuple,
    Protocol,
    TypedDict,
    cast,
)

import httpx

from .errors import PywaUnknownEnumMemberWarning

if TYPE_CHECKING:
    from pywa import WhatsApp


logger = logging.getLogger("pywa.helpers")

DOWNLOAD_CHUNK_SIZE = 64 * 1024
USE_FAKE_GEN_STREAM = True


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field[Any]]]


class StrEnum(str, enum.Enum):
    """A string-based enum with forward compatibility for unknown API values."""

    _normalize: ClassVar[Callable[[str], str] | None] = str.upper
    """
    Normalizes incoming values before attempting a lookup.

    Set to ``None`` to disable normalization.
    """

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{type(self).__name__}.{self.name}"

    @classmethod
    def _missing_(cls, value: object):
        if not isinstance(value, str):
            return super()._missing_(value)
        if cls._normalize is not None:
            member = cls._value2member_map_.get(cls._normalize(value))
            if member is not None:
                return member

        warnings.warn(
            message=(
                f"Unknown {cls.__name__} value: '{value}'"
                f"Defaulting to {cls.__name__}.UNKNOWN.\n"
                "This usually means the WhatsApp API introduced a new value "
                "that your current version of pywa doesn't recognize.\n"
                "Please upgrade to the latest version (`pip install -U pywa`).\n"
                "If you are already on the latest version, please report this at:\n"
                "https://github.com/david-lev/pywa/issues"
            ),
            category=PywaUnknownEnumMemberWarning,
            stacklevel=4,
        )

        try:
            return cls.UNKNOWN  # ty: ignore[unresolved-attribute]
        except AttributeError:
            raise TypeError(
                f"{cls.__name__} must define an UNKNOWN enum member."
            ) from None


class FromDict:
    """Allows to ignore extra fields when creating a dataclass from a dict."""

    # noinspection PyArgumentList
    @classmethod
    def from_dict(cls, data: dict):
        fields = {
            f.name for f in dataclasses.fields(cast("type[DataclassInstance]", cls))
        }
        return cls(**{k: v for k, v in data.items() if k in fields})


class APIObject:
    """Base class for API objects that allows overriding field names."""

    _override_api_fields: ClassVar[dict[str, str]] = {}
    """Override API field names for this object."""

    @classmethod
    @functools.cache
    def _api_fields(cls, *args, **kwargs) -> tuple[str, ...]:
        return tuple(
            cls._override_api_fields.get(f.name, f.name)
            for f in dataclasses.fields(cast("type[DataclassInstance]", cls))
            if not f.name.startswith("_")
        )


def is_async_callable(obj: Any) -> bool:
    """Check if an object is an async callable."""
    return inspect.iscoroutinefunction(obj) or (
        callable(obj) and inspect.iscoroutinefunction(obj.__call__)
    )


from . import utils
from .types.callback import (
    BaseButton,
    Button,
    CallbackData,
)
from .types.flows import FlowJSON, FlowMetricGranularity, FlowMetricName
from .types.media import Media
from .types.others import InteractiveType
from .types.sent_update import RecipientType
from .types.templates import (
    BaseParams,
    Carousel,
    HeaderFormatType,
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    _BaseMediaParams,
)


def resolve_buttons_param(
    buttons: (Iterable[Button] | BaseButton),
) -> tuple[
    InteractiveType,
    dict,
]:
    """
    Internal method to resolve ``buttons`` parameter. Returns a tuple of (``type``, ``buttons``, ``callback_options``).
    """
    if isinstance(buttons, BaseButton):
        return buttons._interactive_type, buttons.to_dict()
    else:  # assume its list of buttons
        try:
            buttons = list(buttons)
        except TypeError:
            raise ValueError(
                f"`buttons` must be a BaseButton or an iterable of Button objects. got {type(buttons)}"
            ) from None
        for b in buttons:
            if not isinstance(b, Button):
                raise TypeError(
                    f"All items in `buttons` iterable must be Button objects. got {type(b)}"
                ) from None
        return InteractiveType.BUTTON, {"buttons": tuple(b.to_dict() for b in buttons)}


header_format_to_media_type: dict[
    HeaderFormatType, Literal["image", "video", "audio", "sticker", "document", "gif"]
] = {
    HeaderFormatType.IMAGE: "image",
    HeaderFormatType.VIDEO: "video",
    HeaderFormatType.DOCUMENT: "document",
    HeaderFormatType.GIF: "gif",
}
media_types_default_filenames = {
    "image": "image.jpg",
    "video": "video.mp4",
    "audio": "audio.mp3",
    "sticker": "sticker.webp",
    "document": "document.pdf",
    "gif": "animation.gif",
}
media_types_default_mime_types = {
    "image": "image/jpeg",
    "video": "video/mp4",
    "audio": "audio/mpeg",
    "sticker": "image/webp",
    "document": "application/pdf",
    "gif": "image/gif",
}
template_header_formats_filename = {
    HeaderFormatType.IMAGE: "image.jpg",
    HeaderFormatType.VIDEO: "video.mp4",
    HeaderFormatType.DOCUMENT: "document.pdf",
    HeaderFormatType.GIF: "animation.gif",
}
template_header_formats_default_mime_types = {
    HeaderFormatType.IMAGE: "image/jpeg",
    HeaderFormatType.VIDEO: "video/mp4",
    HeaderFormatType.DOCUMENT: "application/pdf",
    HeaderFormatType.GIF: "image/gif",
}


class MediaSource(enum.Enum):
    EXTERNAL_URL = enum.auto()  # https:// or http://
    MEDIA_ID = enum.auto()  # 123456789
    MEDIA_OBJ = enum.auto()  # Media(...)
    MEDIA_URL = (
        enum.auto()
    )  # https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=...
    PATH = enum.auto()  # /path/to/file or pathlib.Path
    BYTES = enum.auto()  # b"binary data"
    BYTES_GEN = enum.auto()  # generator yielding bytes
    ASYNC_BYTES_GEN = enum.auto()  # async generator yielding bytes
    FILE_HANDLE = enum.auto()  # "2:c2FtcGxl..."
    FILE_OBJ = enum.auto()  # open("/path/to/file", "rb"), io.BytesIO(b"data"), etc.
    BASE64_DATA_URI = enum.auto()  # data:...;base64,...
    BASE64 = enum.auto()  # "iVBORw0KGgoAAAANSUhEUgAA..."


FILE_HANDLE_PATTERN = re.compile(r"^\d:.*")
BASE64_DATA_URI_PATTERN = re.compile(
    r"^data:(?P<mime>[\w/-]+);base64,(?P<data>[A-Za-z0-9+/]+={0,2})$"
)
BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
WA_MEDIA_PATTERN = re.compile(
    r"^https://lookaside\.fbsbx\.com/whatsapp_business/attachments/\?mid="
)


def detect_media_source(
    media: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
) -> MediaSource:
    source: MediaSource
    if isinstance(media, (str, pathlib.Path, int)):
        media_str = str(media)
        if media_str.startswith(("https://", "http://")):
            if re.match(WA_MEDIA_PATTERN, media_str):
                source = MediaSource.MEDIA_URL
            else:
                source = MediaSource.EXTERNAL_URL
        elif media_str.isdigit():
            source = MediaSource.MEDIA_ID
        elif pathlib.Path(media_str).is_file():
            source = MediaSource.PATH
        elif re.match(FILE_HANDLE_PATTERN, media_str):
            source = MediaSource.FILE_HANDLE
        elif re.match(BASE64_DATA_URI_PATTERN, media_str):
            source = MediaSource.BASE64_DATA_URI
        elif len(media_str) % 4 == 0 and re.match(BASE64_PATTERN, media_str):
            source = MediaSource.BASE64
        else:
            raise ValueError(
                f"String media must be a valid URL, existing file path, WhatsApp media ID, file handle, or base64 string. not: {media_str[:30]}{'...' if len(media_str) > 30 else ''}"
            )
    elif isinstance(media, Media):
        source = MediaSource.MEDIA_OBJ
    elif isinstance(media, bytes):
        source = MediaSource.BYTES
    elif isinstance(media, io.IOBase):
        source = MediaSource.FILE_OBJ
    elif isinstance(media, Iterable):
        source = MediaSource.BYTES_GEN
    elif isinstance(media, AsyncIterable):
        source = MediaSource.ASYNC_BYTES_GEN
    else:
        raise TypeError(f"Invalid media type: {type(media)}")

    logger.debug(
        "Detected media source for %s: %s",
        media
        if source
        not in {
            MediaSource.BYTES,
            MediaSource.FILE_OBJ,
            MediaSource.BYTES_GEN,
            MediaSource.ASYNC_BYTES_GEN,
        }
        else type(media),
        source.name,
    )
    return source


def resolve_media_param(
    *,
    wa: "WhatsApp",
    media: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    mime_type: str | None,
    filename: str | None,
    media_type: Literal["image", "video", "audio", "sticker", "document", "gif"] | None,
    phone_id: str,
) -> tuple[bool, bool, str | Media, str | None]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``uploaded``, ``media/id/url``, ``filename``).
    """
    source = detect_media_source(media)
    match source:
        case MediaSource.EXTERNAL_URL:
            return True, False, str(media), filename or pathlib.Path(str(media)).name
        case MediaSource.MEDIA_ID:
            return False, False, str(media), filename
        case MediaSource.MEDIA_OBJ:
            assert isinstance(media, Media)
            return False, False, media, filename or media.filename
    uploaded_media = internal_upload_media(
        media=media,
        media_source=source,
        media_type=media_type,
        mime_type=mime_type,
        filename=filename,
        download_chunk_size=None,
        wa=wa,
        phone_id=phone_id,
    )
    return False, True, uploaded_media, filename


class GeneratorStreamer(Iterable):
    """
    A MEMORY-EFFICIENT, buffer-free file-like wrapper that lets a bytes generator be
    used where httpx expects a file-like object for multipart/form-data uploads.

    This class intentionally "cheats" httpx by exposing a minimal file-like API
    (read, limited seek, tell) so httpx will treat the underlying generator as a file.
    It does not buffer or store the whole content in memory — it returns chunks
    directly from the provided generator.

    Limitations:

    - read(size) ignores the requested size and returns the next generator chunk.
    - seek() only supports seeking to the end to obtain length (offset=0, whence=os.SEEK_END)
      and a zero-offset SEEK_SET which returns the current read position.
    - tell() returns the total bytes read so far.

    Only use this to make httpx accept generator-based uploads that require a file-like object.
    """

    def __iter__(self):
        return self

    def __init__(self, generator: Iterator[bytes], length: int | None = None):
        self._iterator = itertools.chain(generator, [b""])
        self._length = length
        self._bytes_read = 0

    def read(self, _) -> bytes:
        try:
            chunk = next(self._iterator)
        except StopIteration:
            return b""
        self._bytes_read += len(chunk)
        return chunk

    def seek(self, offset: int, whence: int = 0) -> int:
        if (
            offset == 0 and whence == os.SEEK_END
        ):  # pass https://github.com/encode/httpx/blob/def4778d622e8bf49a9fea4dda78cca4cf666d8a/httpx/_utils.py#L95 check
            if self._length is None:
                raise OSError("Length unknown; cannot seek to end.")
            return self._length

        if offset == 0 and whence == os.SEEK_SET:
            return self._bytes_read

        raise OSError("Cannot seek a streaming object.")

    def tell(self) -> int:
        return self._bytes_read


class MediaInfo(NamedTuple):
    content: (
        bytes | BinaryIO | GeneratorStreamer | Iterator[bytes] | AsyncIterator[bytes]
    )
    filename: str | None
    mime_type: str | None
    length: int | None
    client: httpx.Client | None = None
    cm: Any = None  # context manager to keep alive


def get_media_from_url(
    url: str,
    dl_session: httpx.Client,
    download_chunk_size: int,
    stream: bool,
) -> MediaInfo:
    res = (cm := dl_session.stream("GET", url, follow_redirects=True)).__enter__()
    try:
        res.raise_for_status()
        length: int | None = int(res.headers.get("Content-Length", 0)) or None
        gen = res.iter_bytes(chunk_size=download_chunk_size)
        return MediaInfo(
            content=gen
            if stream
            else (
                GeneratorStreamer(generator=gen, length=length)
                if USE_FAKE_GEN_STREAM
                else b"".join(gen)
            ),
            filename=get_filename_from_httpx_response_headers(res.headers)
            or pathlib.Path(url).name,
            mime_type=res.headers.get("Content-Type") or mimetypes.guess_type(url)[0],
            length=length,
            cm=cm,
        )
    except httpx.HTTPError as e:
        res.close()
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e


def get_media_from_base64(
    base64_str: str,
) -> MediaInfo:
    match = re.match(BASE64_DATA_URI_PATTERN, base64_str)
    if match:
        mime_type = match.group("mime")
        b64_data = match.group("data")
    elif re.match(BASE64_PATTERN, base64_str):
        mime_type = None
        b64_data = base64_str
    else:
        raise ValueError("Invalid base64 string")
    decoded_bytes = base64.b64decode(b64_data)
    return MediaInfo(
        content=decoded_bytes,
        filename=None,
        mime_type=mime_type,
        length=len(decoded_bytes),
    )


def get_media_from_path(
    path: pathlib.Path | str,
) -> MediaInfo:
    p = pathlib.Path(path)
    return MediaInfo(
        content=open(p, "rb"),
        filename=p.name,
        mime_type=mimetypes.guess_type(p)[0],
        length=p.stat().st_size,
    )


def get_media_from_file_like_obj(
    file_obj: BinaryIO,
) -> MediaInfo:
    try:
        length = os.fstat(file_obj.fileno()).st_size
    except (AttributeError, OSError):
        try:
            pos = file_obj.tell()
            file_obj.seek(0, io.SEEK_END)
            length = file_obj.tell()
            file_obj.seek(pos)
        except (AttributeError, OSError):
            length = None
    filename = getattr(file_obj, "name", None)
    return MediaInfo(
        content=file_obj,
        filename=filename,
        mime_type=mimetypes.guess_type(filename)[0] if filename else None,
        length=length,
    )


def get_filename_from_httpx_response_headers(
    headers: httpx.Headers,
) -> str | None:
    content_disposition = headers.get("Content-Disposition")
    if content_disposition:
        parts = content_disposition.split("filename=")
        if len(parts) > 1:
            return parts[1].strip().strip('"').strip("'")
    return None


def get_media_from_media_id_or_obj_or_url(
    wa: "WhatsApp",
    media: str | Media,
    media_source: MediaSource,
    download_chunk_size: int,
    stream: bool,
) -> MediaInfo:
    filename: str | None = None
    mime_type: str | None = None
    url: str | None = None
    match media_source:
        case MediaSource.MEDIA_ID:
            url_res = wa.get_media_url(media_id=str(media))
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_OBJ:
            assert isinstance(media, Media)
            url, mime_type = (
                media.get_media_url(),
                getattr(media, "mime_type", None),
            )
        case MediaSource.MEDIA_URL:
            assert isinstance(media, str)
            url, mime_type = media, None
        case _:
            raise ValueError(
                "media must be MediaSource.MEDIA_ID, MEDIA_OBJ or MEDIA_URL"
            )
    assert url is not None

    res = (cm := wa.api.stream_media_bytes(media_url=url)).__enter__()
    try:
        res.raise_for_status()
    except httpx.HTTPError as e:
        res.close()
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e
    length: int | None = int(res.headers.get("Content-Length", 0)) or None
    gen = res.iter_bytes(chunk_size=download_chunk_size)
    return MediaInfo(
        content=gen
        if stream
        else (
            GeneratorStreamer(generator=gen, length=length)
            if USE_FAKE_GEN_STREAM
            else b"".join(gen)
        ),
        filename=filename or get_filename_from_httpx_response_headers(res.headers),
        mime_type=mime_type or res.headers.get("Content-Type"),
        length=length,
        cm=cm,
    )


def internal_upload_media(
    *,
    media: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    media_source: MediaSource,
    media_type: str | None,
    mime_type: str | None,
    filename: str | None,
    ttl_minutes: int | None = None,
    download_chunk_size: int | None,
    wa: "WhatsApp",
    phone_id: str,
    dl_session: httpx.Client | None = None,
) -> Media:
    """
    Internal method to upload media to WhatsApp servers. Returns a tuple of (``media_id``, ``filename``).
    """
    media_info: MediaInfo | None = None
    client, close_client = None, False

    match media_source:
        case MediaSource.EXTERNAL_URL:
            client, close_client = (
                (dl_session, False) if dl_session else (httpx.Client(), True)
            )
            media_info = get_media_from_url(
                url=str(media),
                dl_session=client,
                download_chunk_size=download_chunk_size or DOWNLOAD_CHUNK_SIZE,
                stream=False,
            )
        case MediaSource.PATH:
            assert isinstance(media, (str, pathlib.Path))
            media_info = get_media_from_path(path=media)
        case MediaSource.BYTES:
            assert isinstance(media, bytes)
            media_info = MediaInfo(
                content=media, filename=None, mime_type=None, length=len(media)
            )
        case MediaSource.FILE_OBJ:
            media_info = get_media_from_file_like_obj(file_obj=cast(BinaryIO, media))
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            assert isinstance(media, (str, Media))
            media_info = get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=media,
                media_source=media_source,
                download_chunk_size=download_chunk_size or DOWNLOAD_CHUNK_SIZE,
                stream=False,
            )
        case MediaSource.BYTES_GEN:
            media = cast(Iterator[bytes], media)
            media_info = MediaInfo(
                content=(
                    GeneratorStreamer(generator=media)
                    if USE_FAKE_GEN_STREAM
                    else b"".join(media)
                ),
                filename=None,
                mime_type=None,
                length=None,
            )
        case MediaSource.BASE64_DATA_URI | MediaSource.BASE64:
            assert isinstance(media, str)
            media_info = get_media_from_base64(base64_str=media)
        case _:
            raise ValueError(
                "Media source must be URL, file path, bytes, bytes generator, file-like object, WhatsApp Media, or base64 string."
            )
    if media_info is None:
        raise ValueError(f"Failed to get media content from {media}")
    final_filename = (
        filename
        or media_info.filename
        or media_types_default_filenames.get(media_type, "file.txt")
    )
    final_mimetype = (
        mime_type
        or media_info.mime_type
        or media_types_default_mime_types.get(media_type, "text/plain")
    )
    try:
        logger.debug(
            "Uploading media to WhatsApp servers: filename=%s, mime_type=%s, length=%s",
            final_filename,
            final_mimetype,
            media_info.length,
        )
        return Media(
            _client=wa,
            _id=wa.api.upload_media(
                phone_id=phone_id,
                media=cast(
                    "bytes | str | BinaryIO | Iterator[bytes] | GeneratorStreamer",
                    media_info.content,
                ),
                mime_type=final_mimetype,
                filename=final_filename,
                ttl_minutes=ttl_minutes,
            )["id"],
            uploaded_to=phone_id,
            filename=final_filename,
            ttl_minutes=ttl_minutes,
        )

    finally:
        try:
            if close_client and client is not None:
                client.close()
            if media_source == MediaSource.PATH:
                media_info.content.close()  # ty: ignore[unresolved-attribute]
        except Exception:  # best-effort cleanup, never mask the real error
            logger.debug("Failed to close media resource during cleanup", exc_info=True)


def filter_not_uploaded_comps(
    components: Sequence[TemplateBaseComponent | dict],
) -> list[_BaseMediaHeaderComponent]:
    not_uploaded = []
    for comp in components:
        if isinstance(comp, _BaseMediaHeaderComponent) and comp._handle is None:
            not_uploaded.append(comp)
        elif isinstance(comp, Carousel):
            for card in comp.cards:
                for cc in card.components:
                    if isinstance(cc, _BaseMediaHeaderComponent) and cc._handle is None:
                        not_uploaded.append(cc)
    return not_uploaded


def upload_template_media_components(
    *,
    wa: "WhatsApp",
    app_id: int | str | None,
    components: Sequence[TemplateBaseComponent | dict],
) -> None:
    """
    Internal method to upload media components examples in a template.
    """
    not_uploaded = filter_not_uploaded_comps(components)
    if not not_uploaded:
        return

    stop_event = threading.Event()
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media"
    ) as executor:
        tasks = [
            executor.submit(
                upload_comps_example,
                wa=wa,
                example=example,
                comps=list(comps),
                app_id=app_id,
                stop_event=stop_event,
            )
            for example, comps in itertools.groupby(
                not_uploaded, key=lambda x: x._example
            )
        ]
        for future in futures.as_completed(tasks):
            future.result()
            if stop_event.is_set():
                break


def internal_upload_file(
    *,
    wa: "WhatsApp",
    file: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    app_id: int | str | None,
    mime_type: str | None,
    fallback_mime_type: str,
    fallback_filename: str | None,
) -> tuple[str, MediaSource]:
    """Internal method to upload a file to Resumable Upload API. Returns a tuple of (``file_handle``, ``media_source``)."""
    media_info: MediaInfo | None = None
    client = None

    source = detect_media_source(file)
    match source:
        case MediaSource.EXTERNAL_URL:
            client = httpx.Client()
            media_info = get_media_from_url(
                url=str(file),
                dl_session=client,
                download_chunk_size=DOWNLOAD_CHUNK_SIZE,
                stream=True,
            )
        case MediaSource.PATH:
            assert isinstance(file, (str, pathlib.Path))
            media_info = get_media_from_path(path=file)
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            assert isinstance(file, (str, Media))
            media_info = get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=file,
                media_source=source,
                download_chunk_size=DOWNLOAD_CHUNK_SIZE,
                stream=True,
            )
        case MediaSource.BYTES:
            assert isinstance(file, bytes)
            media_info = MediaInfo(
                content=file, filename=None, mime_type=None, length=len(file)
            )
        case MediaSource.FILE_OBJ:
            media_info = get_media_from_file_like_obj(cast(BinaryIO, file))
        case MediaSource.BYTES_GEN:
            all_bytes = b"".join(cast("Iterator[bytes]", file))
            media_info = MediaInfo(
                content=all_bytes,
                filename=None,
                mime_type=None,
                length=len(all_bytes),
            )
        case MediaSource.BASE64_DATA_URI | MediaSource.BASE64:
            assert isinstance(file, str)
            media_info = get_media_from_base64(base64_str=file)
        case MediaSource.FILE_HANDLE:
            return str(file), source

    try:
        if not media_info:
            raise ValueError(
                f"Invalid media example for file upload: {file}. "
                "It must be a URL, file path, bytes, file-like object, WhatsApp Media, or file handle."
            )
        if media_info.length is None:
            raise ValueError("Media must have a known length.")
        final_filename = media_info.filename or fallback_filename
        if final_filename is None:
            raise ValueError("Could not determine a filename for the file upload.")
        final_mimetype = mime_type or media_info.mime_type or fallback_mime_type
        logger.debug(
            "Uploading file to Resumable Upload API: filename=%s, mime_type=%s, length=%s",
            final_filename,
            final_mimetype,
            media_info.length,
        )
        return wa.api.upload_file(
            upload_session_id=wa.api.create_upload_session(
                app_id=resolve_arg(
                    wa=wa,
                    value=app_id,
                    method_arg="app_id",
                    client_arg="app_id",
                ),
                file_name=final_filename,
                file_length=media_info.length,
                file_type=final_mimetype,
            )["id"],
            file=cast(
                "bytes | Iterator[bytes] | BinaryIO | GeneratorStreamer",
                media_info.content,
            ),
            file_offset=0,
            content_length=media_info.length,
        )["h"], source

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for file upload with file: {file if not isinstance(file, bytes) else '<bytes>'}: {e}"
        ) from e

    finally:
        try:
            if client:
                client.close()
            if source == MediaSource.PATH:
                media_info.content.close()  # ty: ignore[unresolved-attribute]
        except Exception:  # best-effort cleanup, never mask the real error
            logger.debug("Failed to close media resource during cleanup", exc_info=True)


def upload_comps_example(
    *,
    wa: "WhatsApp",
    example: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    comps: list[_BaseMediaHeaderComponent],
    app_id: int | str | None,
    stop_event: threading.Event,
) -> None:
    if stop_event.is_set():
        return
    first_comp = comps[0]

    try:
        handle, source = internal_upload_file(
            wa=wa,
            file=example,
            app_id=app_id,
            mime_type=first_comp._mime_type,
            fallback_mime_type=template_header_formats_default_mime_types.get(
                first_comp.format, "application/octet-stream"
            ),
            fallback_filename=template_header_formats_filename.get(
                first_comp.format, "pywa-template-header"
            ),
        )
        is_media_obj = source == MediaSource.MEDIA_OBJ
        is_open_file = source == MediaSource.FILE_OBJ
        for comp in comps:
            comp._handle = handle
            if is_media_obj:
                comp._example = cast(Media, comp._example).id
                # prevent keeping Media obj in _example
            if is_open_file:
                try:
                    comp._example = cast(
                        BinaryIO, comp._example
                    ).name  # prevent keeping file obj in _example
                except AttributeError:
                    pass

    except Exception as e:
        stop_event.set()
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {example if not isinstance(example, bytes) else '<bytes>'}: {e}"
        ) from e


def filter_not_uploaded_params(
    params: Sequence[BaseParams | dict],
) -> list[_BaseMediaParams]:
    not_uploaded = []
    for param in params:
        if isinstance(param, _BaseMediaParams) and param._resolved_media is None:
            not_uploaded.append(param)
        elif isinstance(param, Carousel._Params):
            for card_params in param.cards:
                for p in card_params.params:
                    if isinstance(p, _BaseMediaParams) and p._resolved_media is None:
                        not_uploaded.append(p)
    return not_uploaded


def upload_template_media_params(
    *,
    wa: "WhatsApp",
    sender: str,
    params: Sequence[BaseParams | dict],
) -> None:
    """
    Internal method to upload media parameters when sending a template message.
    """
    not_uploaded = filter_not_uploaded_params(params)

    if not not_uploaded:
        return
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media-params"
    ) as executor:
        tasks = [
            executor.submit(
                upload_params_media,
                wa=wa,
                sender=sender,
                media=media,
                params=list(params),
            )
            for media, params in itertools.groupby(not_uploaded, key=lambda x: x.media)
        ]
        for task in futures.wait(tasks)[0]:
            task.result()


def upload_params_media(
    *,
    wa: "WhatsApp",
    sender: str,
    media: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    params: list[_BaseMediaParams],
) -> None:
    first_param = params[0]
    try:
        is_url, uploaded, uploaded_media, fallback_filename = resolve_media_param(
            wa=wa,
            media=media,
            mime_type=first_param._mime_type,
            filename=None,
            media_type=header_format_to_media_type[first_param.format],
            phone_id=sender,
        )
        for p in params:
            p._is_url = is_url
            p._resolved_media = (
                cast(Media, uploaded_media).id
                if uploaded
                else cast(str, uploaded_media)
            )
            p._fallback_filename = fallback_filename
    except Exception as e:
        raise ValueError(
            f"Failed to upload media for parameter {first_param} with media: {media if not isinstance(media, bytes) else '<bytes>'}: {e}"
        ) from e


def resolve_tracker_param(tracker: str | CallbackData | None) -> str | None:
    """Internal method to resolve the `tracker` parameter."""
    return tracker.to_str() if isinstance(tracker, CallbackData) else tracker


BSUID_RE = re.compile(r"^[A-Z]{2}\.\d+$")
WA_ID_RE = re.compile(r"^\d+$")


class _RecipientDict(TypedDict):
    to: str | None
    recipient: str | None
    recipient_type: str


class _CalleeDict(TypedDict):
    to: str | None
    recipient: str | None


def resolve_recipient(to: str | int) -> tuple[_RecipientDict, RecipientType]:
    if not to:
        raise ValueError(f"Recipient cannot be empty. got: {to!r}")
    recipient_type = RecipientType.from_recipient(to)
    logger.debug(f"Resolved recipient {to} to type {recipient_type}")
    to = str(to)
    match recipient_type:
        case RecipientType.WA_ID | RecipientType.PHONE_NUMBER:
            return {
                "to": to,
                "recipient": None,
                "recipient_type": "individual",
            }, recipient_type
        case RecipientType.BSUID | RecipientType.PARENT_BSUID:
            return {
                "to": None,
                "recipient": to,
                "recipient_type": "individual",
            }, recipient_type
        case RecipientType.GROUP_ID:
            return {
                "to": to,
                "recipient": None,
                "recipient_type": "group",
            }, recipient_type
        case _:
            raise ValueError(f"Invalid recipient: {to}")


def clean_phone_number(phone_number: str | int) -> str:
    return re.sub(r"\D", "", str(phone_number))


def resolve_callee(to: str | int) -> tuple[_CalleeDict, RecipientType]:
    recipient, recipient_type = resolve_recipient(to)
    return {"to": recipient["to"], "recipient": recipient["recipient"]}, recipient_type


def resolve_call_permission_request_user(user_id: int | str) -> dict[str, str]:
    _, recipient_type = resolve_recipient(user_id)
    match recipient_type:
        case RecipientType.WA_ID | RecipientType.PHONE_NUMBER:
            return {"user_wa_id": clean_phone_number(user_id)}
        case RecipientType.BSUID | RecipientType.PARENT_BSUID:
            return {"recipient": str(user_id)}
    raise ValueError(f"Invalid recipient type: {recipient_type}")


class _UsersDict(TypedDict):
    users: tuple[str, ...]
    user_ids: tuple[str, ...]


def resolve_users(users: Iterable[str | int]) -> _UsersDict:
    resolved_users: list[str] = []
    resolved_user_ids: list[str] = []
    for user_id in users:
        _, recipient_type = resolve_recipient(user_id)
        match recipient_type:
            case RecipientType.WA_ID | RecipientType.PHONE_NUMBER:
                resolved_users.append(str(user_id))
            case RecipientType.BSUID | RecipientType.PARENT_BSUID:
                resolved_user_ids.append(str(user_id))
            case _:
                raise ValueError(f"Invalid recipient type: {recipient_type}")
    return {"users": tuple(resolved_users), "user_ids": tuple(resolved_user_ids)}


def resolve_arg(
    *,
    wa: "WhatsApp",
    value: str | int | None,
    method_arg: str,
    client_arg: str,
) -> str:
    if value is not None:
        return str(value)
    if getattr(wa, client_arg, None) is not None:
        return str(getattr(wa, client_arg))
    raise ValueError(
        f"When initializing WhatsApp without `{client_arg}`, `{method_arg}` must be provided."
    )


def resolve_flow_json_param(
    flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO,
) -> str:
    """Internal method to solve the `flow_json` parameter"""
    json_str: str | None = None
    to_dump = None
    if isinstance(flow_json, (str, pathlib.Path)):  # json str or path to json file
        as_path = pathlib.Path(flow_json)
        try:
            if as_path.is_file():
                with open(as_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
            else:
                json_str = str(flow_json)
        except OSError:
            json_str = str(flow_json)
    elif isinstance(flow_json, bytes):
        json_str = flow_json.decode()
    elif isinstance(flow_json, FlowJSON):
        json_str = flow_json.to_json()
    elif isinstance(flow_json, dict):
        to_dump = flow_json
    elif isinstance(flow_json, io.IOBase):
        json_str = flow_json.read().decode()
    else:
        raise TypeError(
            f"`flow_json` must be a FlowJSON object, dict, json string, json file path or json bytes. not {type(flow_json)}"
        )

    if to_dump is not None:
        json_str = json.dumps(to_dump, indent=4, ensure_ascii=False)

    assert json_str is not None
    return json_str


def get_interactive_msg(
    typ: InteractiveType,
    action: dict[str, Any],
    header: dict | None = None,
    body: str | None = None,
    footer: str | None = None,
):
    return {
        "type": typ.value,
        "action": action,
        **({"header": header} if header else {}),
        **({"body": {"text": body}} if body else {}),
        **({"footer": {"text": footer}} if footer else {}),
    }


def get_media_msg(
    media: str | Media,
    is_url: bool,
    caption: str | None = None,
    filename: str | None = None,
    is_voice: bool | None = None,
    is_interactive: bool = False,
):
    return {
        ("link" if is_url else "id"): media
        if is_url or not isinstance(media, Media)
        else media.id,
        **(
            {"caption": caption} if caption and not is_interactive else {}
        ),  # caption not supported in interactive media messages
        **({"filename": filename} if filename else {}),
        **({"voice": is_voice} if is_voice is not None else {}),
    }


def get_flow_metric_field(
    metric_name: FlowMetricName,
    granularity: FlowMetricGranularity,
    since: datetime.date | str | None,
    until: datetime.date | str | None,
) -> str:
    date_fmt = "%Y-%m-%d"
    return (
        f"metric.name({metric_name}).granularity({granularity})"
        + (
            f".since({since.strftime(date_fmt) if isinstance(since, datetime.date) else since})"
            if since
            else ""
        )
        + (
            f".until({until.strftime(date_fmt) if isinstance(until, datetime.date) else until})"
            if until
            else ""
        )
    )


def resolve_callback_data(data: str | CallbackData) -> str:
    """Internal function to convert callback data to a string."""
    if isinstance(data, CallbackData):
        return data.to_str()
    elif isinstance(data, str):
        return data
    raise TypeError(f"Invalid callback data type {type(data)}")


def is_installed(lib: str) -> bool:
    """Check if the library is installed."""
    return importlib.util.find_spec(lib) is not None


def rename_func(extended_with: str) -> Callable:
    """Rename function to avoid conflicts when registering the same function multiple times."""

    def inner(func: types.FunctionType):
        func.__name__ = f"{func.__name__}{extended_with}"
        return func

    return inner


def timestamp_to_datetime(ts: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)


def register_routes_starlette(wa: "WhatsApp"):
    from starlette.applications import Starlette as StarletteApp
    from starlette.background import BackgroundTask as StarletteBackgroundTask
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    server = cast(StarletteApp, wa._server)

    async def _webhook_challenge_handler(
        req: StarletteRequest,
    ) -> StarletteResponse:
        params = req.query_params
        vt, ch = params.get(utils.HUB_VT), params.get(utils.HUB_CH)
        content, status = (
            (
                await wa.webhook_challenge_handler(  # ty: ignore[invalid-await]
                    vt=vt,
                    ch=ch,
                )
            )
            if wa._async_allowed
            else wa.webhook_challenge_handler(vt=vt, ch=ch)
        )
        return StarletteResponse(
            content=content,
            status_code=status,
            media_type="text/plain",
            headers={
                "X-Content-Type-Options": "nosniff",
            },
        )

    async def _webhook_update_handler(req: StarletteRequest) -> StarletteResponse:
        body = await req.body()
        if error := (
            (
                await wa.webhook_update_validator(  # ty: ignore[invalid-await]
                    update=body, hmac_header=req.headers.get(utils.HUB_SIG)
                )
            )
            if wa._async_allowed
            else wa.webhook_update_validator(
                update=body, hmac_header=req.headers.get(utils.HUB_SIG)
            )
        ):
            return StarletteResponse(
                content=error[0],
                status_code=error[1],
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )

        bg_task = StarletteBackgroundTask(
            wa.webhook_update_handler,
            body,
        )
        return StarletteResponse(
            content="OK",
            status_code=200,
            headers={
                "X-Content-Type-Options": "nosniff",
            },
            background=bg_task,
        )

    server.add_route(
        path=wa._webhook_endpoint,
        route=_webhook_challenge_handler,
        methods=["GET"],
        include_in_schema=False,
    )
    server.add_route(
        path=wa._webhook_endpoint,
        route=_webhook_update_handler,
        methods=["POST"],
        include_in_schema=False,
    )


def register_routes_fastapi(
    wa: "WhatsApp",
):
    import fastapi

    server = cast(fastapi.FastAPI, wa._server)

    @server.get(wa._webhook_endpoint, include_in_schema=False)
    async def pywa_challenge(
        vt: str = fastapi.Query(alias=utils.HUB_VT, examples=["xyzxyz"]),
        ch: str = fastapi.Query(alias=utils.HUB_CH, examples=["1858252904"]),
    ) -> fastapi.Response:
        """Automatically generated by pywa to handle the verification challenge."""
        content, status = (
            (
                await wa.webhook_challenge_handler(  # ty: ignore[invalid-await]
                    vt=vt,
                    ch=ch,
                )
            )
            if wa._async_allowed
            else wa.webhook_challenge_handler(vt=vt, ch=ch)
        )
        return fastapi.Response(
            content=content,
            status_code=status,
            media_type="text/plain",
            headers={
                "X-Content-Type-Options": "nosniff",
            },
        )

    @server.post(wa._webhook_endpoint, include_in_schema=False)
    async def pywa_webhook(
        bg_tasks: fastapi.BackgroundTasks,
        req: fastapi.Request,
        hmac_header: str = fastapi.Header(alias=utils.HUB_SIG, examples=["sha256=..."]),
    ) -> fastapi.Response:
        """Automatically generated by pywa to handle incoming updates."""
        update: bytes = await req.body()
        if error := (
            (
                await wa.webhook_update_validator(  # ty: ignore[invalid-await]
                    update=update, hmac_header=hmac_header
                )
            )
            if wa._async_allowed
            else wa.webhook_update_validator(update=update, hmac_header=hmac_header)
        ):
            return fastapi.Response(
                content=error[0],
                status_code=error[1],
                media_type="text/plain",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )
        bg_tasks.add_task(
            wa.webhook_update_handler,
            update=update,
        )
        return fastapi.Response(
            content="OK",
            status_code=200,
            media_type="text/plain",
            headers={
                "X-Content-Type-Options": "nosniff",
            },
        )


def register_routes_flask(
    wa: "WhatsApp",
):
    import flask

    server = cast(flask.Flask, wa._server)

    if wa._async_allowed:
        if not is_installed("asgiref"):  # flask[async]
            raise ValueError(
                "Flask with ASGI is required to handle incoming updates asynchronously. Please install "
                """the `asgiref` package (`pip install "flask[async]"` / `pip install "asgiref"`)"""
            )

        @server.route(wa._webhook_endpoint, methods=["GET"])
        @rename_func(f"('{wa._webhook_endpoint}')")
        async def pywa_challenge() -> flask.Response:
            """Automatically generated by pywa to handle the verification challenge."""
            ch, code = await wa.webhook_challenge_handler(  # ty: ignore[invalid-await]
                vt=flask.request.args.get(utils.HUB_VT),
                ch=flask.request.args.get(utils.HUB_CH),
            )
            return flask.Response(
                response=ch,
                status=code,
                content_type="text/plain",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )

        @server.route(wa._webhook_endpoint, methods=["POST"])
        @rename_func(f"('{wa._webhook_endpoint}')")
        async def pywa_webhook() -> flask.Response:
            """Automatically generated by pywa to handle incoming updates."""
            update = flask.request.data
            if error := await wa.webhook_update_validator(  # ty: ignore[invalid-await]
                update=update,
                hmac_header=flask.request.headers.get(utils.HUB_SIG),
            ):
                return flask.Response(
                    response=error[0],
                    status=error[1],
                    content_type="text/plain",
                    headers={
                        "X-Content-Type-Options": "nosniff",
                    },
                )
            res, status = await wa.webhook_update_handler(  # ty: ignore[invalid-await]
                update=update,
            )
            return flask.Response(
                response=res,
                status=status,
                content_type="text/plain",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )

    else:

        @server.route(wa._webhook_endpoint, methods=["GET"])
        @rename_func(f"('{wa._webhook_endpoint}')")
        def pywa_challenge() -> flask.Response:
            """Automatically generated by pywa to handle the verification challenge."""
            ch, code = wa.webhook_challenge_handler(
                vt=flask.request.args.get(utils.HUB_VT),
                ch=flask.request.args.get(utils.HUB_CH),
            )
            return flask.Response(
                response=ch,
                status=code,
                content_type="text/plain",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )

        @server.route(wa._webhook_endpoint, methods=["POST"])
        @rename_func(f"('{wa._webhook_endpoint}')")
        def pywa_webhook() -> flask.Response:
            """Automatically generated by pywa to handle incoming updates."""
            update = flask.request.data
            if error := wa.webhook_update_validator(
                update=update,
                hmac_header=flask.request.headers.get(utils.HUB_SIG),
            ):
                return flask.Response(
                    response=error[0],
                    status=error[1],
                    content_type="text/plain",
                    headers={
                        "X-Content-Type-Options": "nosniff",
                    },
                )
            res, status = wa.webhook_update_handler(
                update=update,
            )
            return flask.Response(
                response=res,
                status=status,
                content_type="text/plain",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )


from .handlers import FlowRequestCallbackWrapper


def register_flow_endpoint_starlette(
    wa: "WhatsApp",
    callback_wrapper: FlowRequestCallbackWrapper,
) -> None:
    import anyio.from_thread
    from starlette.applications import Starlette as StarletteApp
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    server = cast(StarletteApp, wa._server)

    if wa._async_allowed:

        async def pywa_flow(
            req: StarletteRequest,
        ) -> StarletteResponse:
            """Automatically generated by pywa to handle incoming flow requests."""
            response, status_code = await callback_wrapper.handle_async(
                await req.json()
            )
            return StarletteResponse(
                content=response,
                status_code=status_code,
                media_type="application/json",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )
    else:

        def pywa_flow(
            req: StarletteRequest,
        ) -> StarletteResponse:
            """Automatically generated by pywa to handle incoming flow requests."""
            response, status_code = callback_wrapper.handle(
                anyio.from_thread.run(req.json)
            )
            return StarletteResponse(
                content=response,
                status_code=status_code,
                media_type="application/json",
                headers={
                    "X-Content-Type-Options": "nosniff",
                },
            )

    server.add_route(
        path=callback_wrapper._endpoint,
        route=pywa_flow,
        methods=["POST"],
        include_in_schema=False,
    )


def register_flow_endpoint_fastapi(
    wa: "WhatsApp",
    callback_wrapper: FlowRequestCallbackWrapper,
) -> None:
    import fastapi

    server = cast(fastapi.FastAPI, wa._server)

    async def _process_request(request: fastapi.Request) -> tuple[str, int]:
        req_dict = await request.json()
        return (
            (await callback_wrapper.handle_async(req_dict))
            if wa._async_allowed
            else callback_wrapper.handle(req_dict)
        )

    @server.post(callback_wrapper._endpoint, include_in_schema=False)
    async def pywa_flow(
        res: tuple[str, int] = fastapi.Depends(_process_request),
    ) -> fastapi.Response:
        """Automatically generated by pywa to handle incoming flow requests."""
        response, status_code = res
        return fastapi.Response(
            content=response,
            status_code=status_code,
        )


def register_flow_endpoint_flask(
    wa: "WhatsApp",
    callback_wrapper: FlowRequestCallbackWrapper,
) -> FlowRequestCallbackWrapper:
    import flask

    server = cast(flask.Flask, wa._server)

    if wa._async_allowed:
        if not is_installed("asgiref"):  # flask[async]
            raise ValueError(
                "Flask with ASGI is required to handle incoming flow requests asynchronously. Please install "
                """the `asgiref` package (`pip install "flask[async]"` / `pip install "asgiref"`)"""
            )

        @server.route(callback_wrapper._endpoint, methods=["POST"])
        @rename_func(f"('{callback_wrapper._endpoint}')")
        async def pywa_flow() -> tuple[str, int]:
            """Automatically generated by pywa to handle incoming flow requests."""
            return await callback_wrapper.handle_async(flask.request.json)

    else:

        @server.route(callback_wrapper._endpoint, methods=["POST"])
        @rename_func(f"('{callback_wrapper._endpoint}')")
        def pywa_flow() -> tuple[str, int]:
            """Automatically generated by pywa to handle incoming flow requests."""
            return callback_wrapper.handle(flask.request.json)

    return callback_wrapper
