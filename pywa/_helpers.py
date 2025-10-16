from __future__ import annotations

__all__ = [
    "resolve_buttons_param",
    "resolve_media_param",
    "resolve_tracker_param",
    "resolve_arg",
    "upload_template_media_components",
    "resolve_flow_json_param",
    "get_interactive_msg",
    "get_media_msg",
    "get_flow_metric_field",
    "resolve_callback_data",
]

import base64
import datetime
import enum
import io
import itertools
import json
import logging
import mimetypes
import os
import pathlib
import re
import threading
from concurrent import futures
from typing import Any, BinaryIO, Iterable, TYPE_CHECKING, NamedTuple, Literal, Iterator

import httpx

from .types import (
    FlowMetricName,
    FlowMetricGranularity,
    FlowJSON,
    CallbackData,
    URLButton,
    VoiceCallButton,
    SectionList,
    FlowButton,
    Button,
    CallPermissionRequestButton,
    ButtonUrl,
)
from pywa.types.others import InteractiveType
from .types.media import Media
from .types.templates import (
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    HeaderFormatType,
    Carousel,
    _BaseMediaParams,
    BaseParams,
)

if TYPE_CHECKING:
    from pywa import WhatsApp


_logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024


def resolve_buttons_param(
    buttons: (
        Iterable[Button]
        | URLButton
        | VoiceCallButton
        | CallPermissionRequestButton
        | FlowButton
        | SectionList
    ),
) -> tuple[
    InteractiveType,
    dict,
]:
    """
    Internal method to resolve ``buttons`` parameter. Returns a tuple of (``type``, ``buttons``, ``callback_options``).
    """
    if isinstance(buttons, SectionList):
        data = buttons.to_dict()
        return (
            InteractiveType.LIST,
            data,
        )
    elif isinstance(buttons, (URLButton, ButtonUrl)):
        return InteractiveType.CTA_URL, buttons.to_dict()
    elif isinstance(buttons, VoiceCallButton):
        return InteractiveType.VOICE_CALL, buttons.to_dict()
    elif isinstance(buttons, CallPermissionRequestButton):
        return InteractiveType.CALL_PERMISSION_REQUEST, buttons.to_dict()
    elif isinstance(buttons, FlowButton):
        return InteractiveType.FLOW, buttons.to_dict()
    else:  # assume its list of buttons
        return InteractiveType.BUTTON, {"buttons": tuple(b.to_dict() for b in buttons)}


_header_format_to_media_type = {
    HeaderFormatType.IMAGE: "image",
    HeaderFormatType.VIDEO: "video",
    HeaderFormatType.DOCUMENT: "document",
}
_media_types_default_filenames = {
    "image": "image.jpg",
    "video": "video.mp4",
    "audio": "audio.mp3",
    "sticker": "sticker.webp",
    "document": "document.pdf",
}
_media_types_default_mime_types = {
    "image": "image/jpeg",
    "video": "video/mp4",
    "audio": "audio/mpeg",
    "sticker": "image/webp",
    "document": "application/pdf",
}
_template_header_formats_filename = {
    HeaderFormatType.IMAGE: "image.jpg",
    HeaderFormatType.VIDEO: "video.mp4",
    HeaderFormatType.DOCUMENT: "document.pdf",
}
_template_header_formats_default_mime_types = {
    HeaderFormatType.IMAGE: "image/jpeg",
    HeaderFormatType.VIDEO: "video/mp4",
    HeaderFormatType.DOCUMENT: "application/pdf",
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
    FILE_HANDLE = enum.auto()  # "2:c2FtcGxl..."
    FILE_OBJ = enum.auto()  # open("/path/to/file", "rb"), io.BytesIO(b"data"), etc.
    BASE64_DATA_URI = enum.auto()  # data:...;base64,...
    BASE64 = enum.auto()  # "iVBORw0KGgoAAAANSUhEUgAA..."


_MEDIA_ID_PATTERN = re.compile(r"^\d:.*")
_BASE64_DATA_URI_PATTERN = re.compile(
    r"^data:(?P<mime>[\w/-]+);base64,(?P<data>[A-Za-z0-9+/]+={0,2})$"
)
_BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def detect_media_source(
    media: str | int | Media | pathlib.Path | bytes | BinaryIO | Iterator[bytes],
) -> MediaSource:
    if isinstance(media, (str, pathlib.Path, int)):
        media = str(media)
        if media.startswith(("https://", "http://")):
            if re.match(
                r"^https://lookaside\.fbsbx\.com/whatsapp_business/attachments/\?mid=",
                media,
            ):
                _logger.debug("Detected media source as WhatsApp media URL")
                return MediaSource.MEDIA_URL
            _logger.debug("Detected media source as external URL")
            return MediaSource.EXTERNAL_URL
        elif media.isdigit():
            _logger.debug("Detected media source as WhatsApp media ID")
            return MediaSource.MEDIA_ID
        elif pathlib.Path(media).is_file():
            _logger.debug("Detected media source as file path")
            return MediaSource.PATH
        elif re.match(_MEDIA_ID_PATTERN, media):
            _logger.debug("Detected media source as file handle")
            return MediaSource.FILE_HANDLE
        elif re.match(_BASE64_DATA_URI_PATTERN, media):
            _logger.debug("Detected media source as base64 data URI")
            return MediaSource.BASE64_DATA_URI
        elif len(media) % 4 == 0 and re.match(_BASE64_PATTERN, media):
            _logger.debug("Detected media source as base64 string")
            return MediaSource.BASE64
        else:
            raise ValueError(
                f"String media must be a valid URL, existing file path, WhatsApp media ID, file handle, or base64 string. not: {media[:30]}{'...' if len(media) > 30 else ''}"
            )
    elif isinstance(media, Media):
        _logger.debug("Detected media source as WhatsApp Media object")
        return MediaSource.MEDIA_OBJ
    elif isinstance(media, bytes):
        _logger.debug("Detected media source as bytes")
        return MediaSource.BYTES
    elif isinstance(media, io.IOBase):
        _logger.debug("Detected media source as file like object")
        return MediaSource.FILE_OBJ
    elif callable(getattr(media, "__iter__", None)) and not isinstance(
        media, (str, bytes, bytearray)
    ):
        _logger.debug("Detected media source as bytes generator")
        return MediaSource.BYTES_GEN
    else:
        raise TypeError(f"Invalid media type: {type(media)}")


def resolve_media_param(
    *,
    wa: WhatsApp,
    media: str | int | Media | pathlib.Path | bytes | BinaryIO | Iterator[bytes],
    mime_type: str | None,
    filename: str | None,
    media_type: Literal["image", "video", "audio", "sticker", "document"] | None,
    phone_id: str,
) -> tuple[bool, str, str]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``media_id_or_url``, ``filename``).
    """
    source = detect_media_source(media)
    match source:
        case MediaSource.EXTERNAL_URL:
            return True, str(media), filename or pathlib.Path(media).name
        case MediaSource.MEDIA_ID:
            return False, str(media), filename
        case MediaSource.MEDIA_OBJ:
            return False, media.id, filename
    media_id, filename = internal_upload_media(
        media=media,
        media_source=source,
        media_type=media_type,
        mime_type=mime_type,
        filename=filename,
        wa=wa,
        phone_id=phone_id,
    )
    return False, media_id, filename


class _IteratorStream:
    def __init__(self, iterator: Iterator[bytes], length: int | None = None):
        self.iterator = iterator
        self._buffer = b""
        self._done = False
        self.length = length

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if self._done:
            return b""

        if size < 0:
            chunks = [self._buffer]
            self._buffer = b""
            for chunk in self.iterator:
                if not chunk:
                    break
                chunks.append(chunk)
            self._done = True
            return b"".join(chunks)

        data = bytearray(self._buffer)
        self._buffer = b""

        while len(data) < size:
            try:
                chunk = next(self.iterator)
            except StopIteration:
                self._done = True
                break
            except Exception:
                self._done = True
                raise
            if not chunk:
                self._done = True
                break
            data.extend(chunk)

        if len(data) > size:
            self._buffer = bytes(data[size:])
            data = data[:size]

        return bytes(data)


class MediaInfo(NamedTuple):
    content: bytes | BinaryIO | _IteratorStream
    filename: str | None
    mime_type: str | None
    length: int | None
    client: httpx.Client | None = None
    cm: Any = None  # context manager to keep alive


def _get_media_from_url(
    url: str,
    dl_session: httpx.Client,
) -> MediaInfo:
    res = (cm := dl_session.stream("GET", url)).__enter__()
    try:
        res.raise_for_status()
        return MediaInfo(
            content=_IteratorStream(res.iter_bytes(chunk_size=CHUNK_SIZE)),
            filename=_get_filename_from_httpx_response_headers(res.headers)
            or pathlib.Path(url).name,
            mime_type=res.headers.get("Content-Type") or mimetypes.guess_type(url)[0],
            length=int(res.headers.get("Content-Length", 0)) or None,
            cm=cm,
        )
    except httpx.HTTPError as e:
        res.close()
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e


def _get_media_from_base64(
    base64_str: str,
) -> MediaInfo:
    match = re.match(_BASE64_DATA_URI_PATTERN, base64_str)
    if match:
        mime_type = match.group("mime")
        b64_data = match.group("data")
    elif re.match(_BASE64_PATTERN, base64_str):
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


def _get_media_from_path(
    path: pathlib.Path | str,
) -> MediaInfo:
    p = pathlib.Path(path)
    return MediaInfo(
        content=open(p, "rb"),
        filename=p.name,
        mime_type=mimetypes.guess_type(p)[0],
        length=p.stat().st_size,
    )


def _get_media_from_file_like_obj(
    file_obj: BinaryIO,
) -> MediaInfo:
    try:
        length = os.fstat(file_obj.fileno()).st_size
    except (AttributeError, OSError):
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


def _get_filename_from_httpx_response_headers(
    headers: httpx.Headers,
) -> str | None:
    content_disposition = headers.get("Content-Disposition")
    if content_disposition:
        parts = content_disposition.split("filename=")
        if len(parts) > 1:
            return parts[1].strip().strip('"').strip("'")
    return None


def _get_media_from_media_id_or_obj_or_url(
    wa: WhatsApp,
    media: str | Media,
    media_source: MediaSource,
) -> MediaInfo:
    filename: str | None = None
    mime_type: str | None = None
    url: str | None = None
    match media_source:
        case MediaSource.MEDIA_ID:
            url_res = wa.get_media_url(media_id=str(media))
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_OBJ:
            url_res = wa.get_media_url(media_id=media.id)
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_URL:
            url, mime_type = media, None
        case _:
            raise ValueError(
                "media must be MediaSource.MEDIA_ID, MEDIA_OBJ or MEDIA_URL"
            )

    res = (cm := wa.api.get_media_bytes(media_url=url)).__enter__()
    try:
        res.raise_for_status()
    except httpx.HTTPError as e:
        res.close()
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e
    return MediaInfo(
        content=_IteratorStream(res.iter_bytes(chunk_size=CHUNK_SIZE)),
        filename=filename or _get_filename_from_httpx_response_headers(res.headers),
        mime_type=mime_type or res.headers.get("Content-Type"),
        length=int(res.headers.get("Content-Length", 0)) or None,
        cm=cm,
    )


def internal_upload_media(
    *,
    media: str | int | Media | pathlib.Path | bytes | BinaryIO | Iterator[bytes],
    media_source: MediaSource,
    media_type: str | None,
    mime_type: str | None,
    filename: str | None,
    wa: WhatsApp,
    phone_id: str,
    dl_session: httpx.Client | None = None,
) -> tuple[str, str]:
    """
    Internal method to upload media to WhatsApp servers. Returns a tuple of (``media_id``, ``filename``).
    """
    media_info: MediaInfo | None = None
    client, close_client = None, False

    match media_source:
        case MediaSource.EXTERNAL_URL:
            client, close_client = (
                (dl_session, False)
                if dl_session
                else (httpx.Client(follow_redirects=True), True)
            )
            media_info = _get_media_from_url(url=media, dl_session=client)
        case MediaSource.PATH:
            media_info = _get_media_from_path(path=media)
        case MediaSource.BYTES:
            media_info = MediaInfo(
                content=media, filename=None, mime_type=None, length=len(media)
            )
        case MediaSource.FILE_OBJ:
            media_info = _get_media_from_file_like_obj(file_obj=media)
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            media_info = _get_media_from_media_id_or_obj_or_url(
                wa=wa, media=media, media_source=media_source
            )
        case MediaSource.BYTES_GEN:
            media_info = MediaInfo(
                content=_IteratorStream(media),
                filename=None,
                mime_type=None,
                length=None,
            )
        case MediaSource.BASE64_DATA_URI, MediaSource.BASE64:
            media_info = _get_media_from_base64(base64_str=media)
        case _:
            raise ValueError(
                "Media source must be URL, file path, bytes, file-like object, WhatsApp Media, or base64 string."
            )
    if media_info is None:
        raise ValueError(f"Failed to get media content from {media}")
    final_filename = (
        filename
        or media_info.filename
        or _media_types_default_filenames.get(media_type, "file.txt")
    )
    try:
        return wa.api.upload_media(
            phone_id=phone_id,
            media=media_info.content,
            mime_type=mime_type
            or media_info.mime_type
            or _media_types_default_mime_types.get(media_type, "text/plain"),
            filename=final_filename,
        )["id"], final_filename
    finally:
        try:  # close file or stream
            media_info.content.close()  # type: ignore
            if close_client:
                client.close()  # type: ignore
        except Exception:
            pass


def _filter_not_uploaded_comps(
    components: list[TemplateBaseComponent | dict],
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
    wa: WhatsApp,
    app_id: int | str | None,
    components: list[TemplateBaseComponent | dict],
) -> None:
    """
    Internal method to upload media components examples in a template.
    """
    not_uploaded = _filter_not_uploaded_comps(components)
    if not not_uploaded:
        return

    stop_event = threading.Event()
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media"
    ) as executor:
        tasks = [
            executor.submit(
                _upload_comps_example,
                wa=wa,
                example=example,
                comps=list(comps),
                app_id=app_id,
                stop_event=stop_event,
            )
            for example, comps in itertools.groupby(
                not_uploaded, key=lambda x: x.example
            )
        ]
        for future in futures.as_completed(tasks):
            future.result()
            if stop_event.is_set():
                break


def _upload_comps_example(
    *,
    wa: WhatsApp,
    example: str | Media | pathlib.Path | bytes | BinaryIO,
    comps: list[_BaseMediaHeaderComponent],
    app_id: int | str | None,
    stop_event: threading.Event,
) -> None:
    if stop_event.is_set():
        return
    first_comp = comps[0]
    media_info: MediaInfo | None = None
    client = None

    source = detect_media_source(example)
    match source:
        case MediaSource.EXTERNAL_URL:
            client = httpx.Client(follow_redirects=True)
            media_info = _get_media_from_url(url=example, dl_session=client)
        case MediaSource.PATH:
            media_info = _get_media_from_path(path=example)
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            media_info = _get_media_from_media_id_or_obj_or_url(
                wa=wa, media=example, media_source=source
            )
        case MediaSource.BYTES:
            media_info = MediaInfo(
                content=example, filename=None, mime_type=None, length=len(example)
            )
        case MediaSource.FILE_OBJ:
            media_info = _get_media_from_file_like_obj(example)
        case MediaSource.FILE_HANDLE:
            for comp in comps:
                comp._handle = example
            return

    try:
        if not media_info:
            raise ValueError(
                f"Invalid media example for component {first_comp.__class__.__name__}: {example}. "
                "It must be a URL, file path, bytes, file-like object, WhatsApp Media, or file handle."
            )
        if media_info.length is None:
            raise ValueError(
                f"Media example for component {first_comp.__class__.__name__} must have a known length."
            )
        handle = wa.api.upload_file(
            upload_session_id=wa.api.create_upload_session(
                app_id=resolve_arg(
                    wa=wa,
                    value=app_id,
                    method_arg="app_id",
                    client_arg="app_id",
                ),
                file_name=media_info.filename
                or _template_header_formats_filename.get(
                    first_comp.format, "pywa-template-header"
                ),
                file_length=media_info.length,
                file_type=media_info.mime_type
                or _template_header_formats_default_mime_types.get(
                    first_comp.format, "application/octet-stream"
                ),
            )["id"],
            file=media_info.content,
            file_offset=0,
        )["h"]

        for comp in comps:
            comp._handle = handle

    except Exception as e:
        stop_event.set()
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {example if not isinstance(example, bytes) else '<bytes>'}"
        ) from e

    finally:
        if client:
            client.close()


def _filter_not_uploaded_params(
    params: list[BaseParams | dict],
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
    wa: WhatsApp,
    sender: str,
    params: list[BaseParams | dict],
) -> None:
    """
    Internal method to upload media parameters when sending a template message.
    """
    not_uploaded = _filter_not_uploaded_params(params)

    if not not_uploaded:
        return
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media-params"
    ) as executor:
        tasks = [
            executor.submit(
                _upload_params_media,
                wa=wa,
                sender=sender,
                media=media,
                params=list(params),
            )
            for media, params in itertools.groupby(not_uploaded, key=lambda x: x.media)
        ]
        for task in futures.wait(tasks)[0]:
            task.result()


def _upload_params_media(
    *,
    wa: WhatsApp,
    sender: str,
    media: str | Media | pathlib.Path | bytes | BinaryIO,
    params: list[_BaseMediaParams],
) -> None:
    first_param = params[0]
    try:
        is_url, media_id_or_url, fallback_filename = resolve_media_param(
            wa=wa,
            media=media,
            mime_type=None,
            filename=None,
            media_type=_header_format_to_media_type[first_param.format],
            phone_id=sender,
        )
        for p in params:
            p._is_url = is_url
            p._resolved_media = media_id_or_url
            p._fallback_filename = fallback_filename

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for parameter {first_param} with media: {media if not isinstance(media, bytes) else '<bytes>'}"
        ) from e


def resolve_tracker_param(tracker: str | CallbackData | None) -> str | None:
    """Internal method to resolve the `tracker` parameter."""
    return tracker.to_str() if isinstance(tracker, CallbackData) else tracker


def resolve_arg(
    *,
    wa: WhatsApp,
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
    json_str, to_dump = None, None
    if isinstance(flow_json, (str, pathlib.Path)):  # json str or path to json file
        as_path = pathlib.Path(flow_json)
        try:
            if as_path.is_file():
                with open(as_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
            else:
                json_str = flow_json
        except OSError:
            json_str = flow_json
    elif isinstance(flow_json, bytes):
        json_str = flow_json.decode()
    elif isinstance(flow_json, FlowJSON):
        json_str = flow_json.to_json()
    elif isinstance(flow_json, dict):
        to_dump = flow_json
    else:
        raise TypeError(
            f"`flow_json` must be a FlowJSON object, dict, json string, json file path or json bytes. not {type(flow_json)}"
        )

    if to_dump is not None:
        json_str = json.dumps(to_dump, indent=4, ensure_ascii=False)

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
    media_id_or_url: str,
    is_url: bool,
    caption: str | None = None,
    filename: str | None = None,
):
    return {
        ("link" if is_url else "id"): media_id_or_url,
        **({"caption": caption} if caption else {}),
        **({"filename": filename} if filename else {}),
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
