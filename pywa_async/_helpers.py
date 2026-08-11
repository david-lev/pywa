import asyncio
import itertools
import mimetypes
import pathlib
from collections.abc import AsyncIterator, Coroutine, Iterator, Sequence
from contextlib import _AsyncGeneratorContextManager
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Literal,
    cast,
)

import httpx

from pywa._helpers import BASE64_DATA_URI_PATTERN as BASE64_DATA_URI_PATTERN
from pywa._helpers import BASE64_PATTERN as BASE64_PATTERN
from pywa._helpers import BSUID_RE as BSUID_RE
from pywa._helpers import DOWNLOAD_CHUNK_SIZE as DOWNLOAD_CHUNK_SIZE
from pywa._helpers import FILE_HANDLE_PATTERN as FILE_HANDLE_PATTERN
from pywa._helpers import USE_FAKE_GEN_STREAM as USE_FAKE_GEN_STREAM
from pywa._helpers import WA_ID_RE as WA_ID_RE
from pywa._helpers import WA_MEDIA_PATTERN as WA_MEDIA_PATTERN

# Import everything from pywa._helpers *except* the names re-implemented as
# `async def` below (resolve_media_param, get_media_from_url,
# get_media_from_media_id_or_obj_or_url, internal_upload_media,
# internal_upload_file, upload_template_media_components,
# upload_template_media_params). Importing those via `*` would leave ty
# treating every call site as ambiguous between the sync and async
# definitions, since both would be visible module-level bindings.
# The `as`-aliases mark these as intentional re-exports (pywa_async.client
# and others access them as `helpers.X`) so ruff doesn't flag them unused.
from pywa._helpers import APIObject as APIObject
from pywa._helpers import FromDict as FromDict
from pywa._helpers import GeneratorStreamer as GeneratorStreamer
from pywa._helpers import MediaInfo as MediaInfo
from pywa._helpers import MediaSource as MediaSource
from pywa._helpers import StrEnum as StrEnum
from pywa._helpers import clean_phone_number as clean_phone_number
from pywa._helpers import detect_media_source as detect_media_source
from pywa._helpers import filter_not_uploaded_comps as filter_not_uploaded_comps
from pywa._helpers import filter_not_uploaded_params as filter_not_uploaded_params
from pywa._helpers import (
    get_filename_from_httpx_response_headers as get_filename_from_httpx_response_headers,
)
from pywa._helpers import get_flow_metric_field as get_flow_metric_field
from pywa._helpers import get_interactive_msg as get_interactive_msg
from pywa._helpers import get_media_from_base64 as get_media_from_base64
from pywa._helpers import get_media_from_file_like_obj as get_media_from_file_like_obj
from pywa._helpers import get_media_from_path as get_media_from_path
from pywa._helpers import get_media_msg as get_media_msg
from pywa._helpers import header_format_to_media_type as header_format_to_media_type
from pywa._helpers import is_async_callable as is_async_callable
from pywa._helpers import is_installed as is_installed
from pywa._helpers import logger as logger
from pywa._helpers import media_types_default_filenames as media_types_default_filenames
from pywa._helpers import (
    media_types_default_mime_types as media_types_default_mime_types,
)
from pywa._helpers import (
    register_flow_endpoint_fastapi as register_flow_endpoint_fastapi,
)
from pywa._helpers import register_flow_endpoint_flask as register_flow_endpoint_flask
from pywa._helpers import (
    register_flow_endpoint_starlette as register_flow_endpoint_starlette,
)
from pywa._helpers import register_routes_fastapi as register_routes_fastapi
from pywa._helpers import register_routes_flask as register_routes_flask
from pywa._helpers import register_routes_starlette as register_routes_starlette
from pywa._helpers import rename_func as rename_func
from pywa._helpers import resolve_arg as resolve_arg
from pywa._helpers import resolve_buttons_param as resolve_buttons_param
from pywa._helpers import (
    resolve_call_permission_request_user as resolve_call_permission_request_user,
)
from pywa._helpers import resolve_callback_data as resolve_callback_data
from pywa._helpers import resolve_callee as resolve_callee
from pywa._helpers import resolve_flow_json_param as resolve_flow_json_param
from pywa._helpers import resolve_recipient as resolve_recipient
from pywa._helpers import resolve_tracker_param as resolve_tracker_param
from pywa._helpers import resolve_users as resolve_users
from pywa._helpers import (
    template_header_formats_default_mime_types as template_header_formats_default_mime_types,
)
from pywa._helpers import (
    template_header_formats_filename as template_header_formats_filename,
)
from pywa._helpers import timestamp_to_datetime as timestamp_to_datetime
from pywa._helpers import upload_comps_example as upload_comps_example
from pywa._helpers import upload_params_media as upload_params_media
from pywa.types.media import Media
from pywa.types.templates import (
    BaseParams,
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    _BaseMediaParams,
)

from .types.media import Media as _AsyncMedia

if TYPE_CHECKING:
    from pywa_async import WhatsApp


async def resolve_media_param(
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
    uploaded_media = await internal_upload_media(
        media=media,
        media_source=source,
        media_type=media_type,
        mime_type=mime_type,
        filename=filename,
        wa=wa,
        phone_id=phone_id,
    )
    return False, True, uploaded_media, filename


async def get_media_from_url(
    url: str,
    dl_session: httpx.AsyncClient,
    download_chunk_size: int | None,
    stream: bool,
) -> MediaInfo:
    if stream:
        res = await (
            cm := dl_session.stream("GET", url, follow_redirects=True)
        ).__aenter__()

    else:
        res, cm = await dl_session.get(url, follow_redirects=True), None
    try:
        res.raise_for_status()
    except httpx.HTTPError as e:
        if stream:
            await res.aclose()
        raise ValueError(f"An error occurred while downloading from {url}") from e

    content_length = int(res.headers.get("Content-Length", "0")) or None
    return MediaInfo(
        content=res.aiter_bytes(chunk_size=download_chunk_size)
        if stream
        else res.content,
        filename=get_filename_from_httpx_response_headers(res.headers)
        or pathlib.Path(url).name,
        mime_type=res.headers.get("Content-Type") or mimetypes.guess_type(url)[0],
        length=content_length if stream else (content_length or len(res.content)),
        cm=cm,
    )


async def get_media_from_media_id_or_obj_or_url(
    wa: "WhatsApp",
    media: str | Media,
    media_source: MediaSource,
    download_chunk_size: int | None,
    stream: bool,
) -> MediaInfo:
    filename: str | None = None
    mime_type: str | None = None
    url: str | None = None
    cm: _AsyncGeneratorContextManager[httpx.Response] | None = None
    match media_source:
        case MediaSource.MEDIA_ID:
            url_res = await wa.get_media_url(media_id=str(media))
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_OBJ:
            assert isinstance(media, _AsyncMedia)
            url, mime_type = (
                await media.get_media_url(),
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
    if stream:
        res = await (cm := wa.api.stream_media_bytes(media_url=url)).__aenter__()
    else:
        async with wa.api.stream_media_bytes(media_url=url) as res:
            cm, _ = None, await res.aread()
    try:
        res.raise_for_status()
    except httpx.HTTPError as e:
        res.close()
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e
    content_length = int(res.headers.get("Content-Length", "0")) or None
    return MediaInfo(
        content=res.aiter_bytes(chunk_size=download_chunk_size)
        if stream
        else res.content,
        filename=filename or get_filename_from_httpx_response_headers(res.headers),
        mime_type=mime_type or res.headers.get("Content-Type"),
        length=content_length if stream else (content_length or len(res.content)),
        cm=cm,
    )


async def internal_upload_media(
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
    wa: "WhatsApp",
    phone_id: str,
    dl_session: httpx.AsyncClient | None = None,
) -> _AsyncMedia:
    """
    Internal method to upload media to WhatsApp servers. Returns a tuple of (``media_id``, ``filename``).
    """
    media_info: MediaInfo | None = None
    client, close_client = None, False

    match media_source:
        case MediaSource.EXTERNAL_URL:
            client, close_client = (
                (dl_session, False) if dl_session else (httpx.AsyncClient(), True)
            )
            media_info = await get_media_from_url(
                url=str(media),
                dl_session=client,
                download_chunk_size=None,
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
            media_info = await get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=media,
                media_source=media_source,
                download_chunk_size=None,
                stream=False,
            )
        case MediaSource.BYTES_GEN:
            media = cast("Iterator[bytes]", media)
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
        case MediaSource.ASYNC_BYTES_GEN:
            media = cast("AsyncIterator[bytes]", media)
            content = b"".join([chunk async for chunk in media])
            media_info = MediaInfo(
                content=content,
                filename=None,
                mime_type=None,
                length=len(content),
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
        return _AsyncMedia(
            _client=wa,
            _id=(
                await wa.api.upload_media(
                    phone_id=phone_id,
                    media=cast(
                        "bytes | str | BinaryIO | Iterator[bytes] | GeneratorStreamer",
                        media_info.content,
                    ),
                    mime_type=final_mimetype,
                    filename=final_filename,
                    ttl_minutes=ttl_minutes,
                )
            )["id"],
            uploaded_to=phone_id,
            filename=final_filename,
            ttl_minutes=ttl_minutes,
        )
    finally:
        try:
            if close_client and client is not None:
                await client.aclose()
            if media_source == MediaSource.PATH:
                media_info.content.close()  # ty: ignore[unresolved-attribute]
        except Exception:  # noqa: BLE001
            logger.debug("Failed to close media resource during cleanup", exc_info=True)


async def upload_template_media_components(
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

    await _run_all_and_cancel_on_exception(
        *[
            _upload_comps_example(
                wa=wa,
                example=example,
                comps=list(comps),
                app_id=app_id,
            )
            for example, comps in itertools.groupby(
                not_uploaded, key=lambda x: x._example
            )
        ]
    )


async def _run_all_and_cancel_on_exception(*coros: Coroutine):
    tasks = [asyncio.create_task(c) for c in coros]

    try:
        return await asyncio.gather(*tasks)
    except Exception:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


async def internal_upload_file(
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
    media_info: MediaInfo | None = None
    client = None

    source = detect_media_source(file)
    match source:
        case MediaSource.EXTERNAL_URL:
            client = httpx.AsyncClient()
            media_info = await get_media_from_url(
                url=str(file),
                dl_session=client,
                download_chunk_size=DOWNLOAD_CHUNK_SIZE,
                stream=True,
            )
        case MediaSource.PATH:
            assert isinstance(file, (str, pathlib.Path))
            p = pathlib.Path(file)
            content = await asyncio.to_thread(p.read_bytes)
            media_info = MediaInfo(
                content=content,
                filename=p.name,
                mime_type=mimetypes.guess_type(p.as_posix())[0],
                length=len(content),
            )
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            assert isinstance(file, (str, Media))
            media_info = await get_media_from_media_id_or_obj_or_url(
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
        case MediaSource.ASYNC_BYTES_GEN:
            all_bytes = b"".join(
                [chunk async for chunk in cast("AsyncIterator[bytes]", file)]
            )
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
        return (
            await wa.api.upload_file(
                upload_session_id=(
                    await wa.api.create_upload_session(
                        app_id=resolve_arg(
                            wa=wa,
                            value=app_id,
                            method_arg="app_id",
                            client_arg="app_id",
                        ),
                        file_name=final_filename,
                        file_length=media_info.length,
                        file_type=final_mimetype,
                    )
                )["id"],
                file=cast(
                    "bytes | AsyncIterator[bytes] | BinaryIO",
                    media_info.content,
                ),
                file_offset=0,
                content_length=media_info.length,
            )
        )["h"], source

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for file upload with file: {file if not isinstance(file, bytes) else '<bytes>'}: {e}"
        ) from e

    finally:
        try:
            if client:
                await client.aclose()
        # best-effort cleanup, never mask the real error
        except Exception:  # noqa: BLE001
            logger.debug("Failed to close media resource during cleanup", exc_info=True)


async def _upload_comps_example(
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
) -> None:
    first_comp = comps[0]

    try:
        handle, source = await internal_upload_file(
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
                comp._example = cast(_AsyncMedia, comp._example).id
                # prevent keeping Media obj in _example
            if is_open_file:
                try:
                    comp._example = cast(
                        BinaryIO, comp._example
                    ).name  # prevent keeping file obj in _example
                except AttributeError:
                    pass

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {example if not isinstance(example, bytes) else '<bytes>'}: {e}"
        ) from e


async def upload_template_media_params(
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

    await _run_all_and_cancel_on_exception(
        *[
            _upload_params_media(
                wa=wa,
                sender=sender,
                media=media,
                params=list(params),
            )
            for media, params in itertools.groupby(not_uploaded, key=lambda x: x.media)
        ]
    )


async def _upload_params_media(
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
        is_url, uploaded, uploaded_media, fallback_filename = await resolve_media_param(
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
