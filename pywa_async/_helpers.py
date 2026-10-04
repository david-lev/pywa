import asyncio
import contextlib
import pathlib
from collections.abc import AsyncIterator, Coroutine, Iterator, Sequence
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
from pywa._helpers import describe_media as describe_media
from pywa._helpers import detect_media_source as detect_media_source
from pywa._helpers import filter_not_uploaded_comps as filter_not_uploaded_comps
from pywa._helpers import filter_not_uploaded_params as filter_not_uploaded_params
from pywa._helpers import (
    get_content_length_from_httpx_response_headers as get_content_length_from_httpx_response_headers,
)
from pywa._helpers import (
    get_filename_from_httpx_response_headers as get_filename_from_httpx_response_headers,
)
from pywa._helpers import get_filename_from_url as get_filename_from_url
from pywa._helpers import get_flow_metric_field as get_flow_metric_field
from pywa._helpers import get_interactive_msg as get_interactive_msg
from pywa._helpers import get_media_from_base64 as get_media_from_base64
from pywa._helpers import get_media_from_file_like_obj as get_media_from_file_like_obj
from pywa._helpers import get_media_from_path as get_media_from_path
from pywa._helpers import get_media_msg as get_media_msg
from pywa._helpers import (
    get_mime_type_from_httpx_response_headers as get_mime_type_from_httpx_response_headers,
)
from pywa._helpers import get_mime_type_from_url as get_mime_type_from_url
from pywa._helpers import group_by_media as group_by_media
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
from pywa._helpers import (
    resolve_media_name_and_type as resolve_media_name_and_type,
)
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
from pywa.errors import WhatsAppError
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
            return (
                True,
                False,
                str(media),
                filename or get_filename_from_url(str(media)),
            )
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


async def aiter_file(file: BinaryIO, chunk_size: int) -> AsyncIterator[bytes]:
    """Stream a file-like object (read in a thread, as httpx's async client can't send a blocking file)."""
    while chunk := await asyncio.to_thread(file.read, chunk_size):
        yield chunk


async def media_info_from_response(
    res: httpx.Response,
    *,
    url: str,
    download_chunk_size: int | None,
    stream: bool,
    mime_type: str | None = None,
    fallback_filename: str | None = None,
    fallback_mime_type: str | None = None,
) -> MediaInfo:
    try:
        res.raise_for_status()
        body = None if stream else await res.aread()
    except httpx.HTTPError as e:
        raise ValueError(f"An error occurred while downloading from {url}: {e}") from e
    if body is None:
        content = res.aiter_bytes(chunk_size=download_chunk_size)
        length = get_content_length_from_httpx_response_headers(res.headers)
    else:
        content, length = body, len(body)
    return MediaInfo(
        content=content,
        filename=get_filename_from_httpx_response_headers(res.headers)
        or fallback_filename,
        mime_type=mime_type
        or get_mime_type_from_httpx_response_headers(res.headers)
        or fallback_mime_type,
        length=length,
    )


async def get_media_from_url(
    stack: contextlib.AsyncExitStack,
    url: str,
    dl_session: httpx.AsyncClient,
    download_chunk_size: int | None,
    stream: bool,
) -> MediaInfo:
    res = await stack.enter_async_context(
        dl_session.stream(
            "GET",
            url,
            follow_redirects=True,
            headers={"Accept-Encoding": "identity"},
        )
    )
    return await media_info_from_response(
        res,
        url=url,
        download_chunk_size=download_chunk_size,
        stream=stream,
        fallback_filename=get_filename_from_url(url),
        fallback_mime_type=get_mime_type_from_url(url),
    )


async def get_media_from_media_id_or_obj_or_url(
    stack: contextlib.AsyncExitStack,
    wa: "WhatsApp",
    media: str | Media,
    media_source: MediaSource,
    download_chunk_size: int | None,
    stream: bool,
) -> MediaInfo:
    mime_type: str | None = None
    url: str | None = None
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
    res = await stack.enter_async_context(wa.api.stream_media_bytes(media_url=url))
    return await media_info_from_response(
        res,
        url=url,
        download_chunk_size=download_chunk_size,
        stream=stream,
        mime_type=mime_type,
    )


async def open_media(
    stack: contextlib.AsyncExitStack,
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
    source: MediaSource,
    stream: bool,
    download_chunk_size: int | None = None,
    dl_session: httpx.AsyncClient | None = None,
) -> MediaInfo:
    """
    Resolve ``media`` into the ``MediaInfo`` to upload.

    Whatever is opened to read it (download client and response, file) is closed with ``stack``, so keep the
    stack open until the upload is done.

    Args:
        stream: An iterator body of a known length (Resumable Upload API) instead of a fully loaded body (multipart upload).
        dl_session: A client to download with (optional, if not provided a new one is created and closed).
    """
    chunk_size = download_chunk_size or DOWNLOAD_CHUNK_SIZE
    match source:
        case MediaSource.EXTERNAL_URL:
            return await get_media_from_url(
                stack,
                url=str(media),
                dl_session=dl_session
                or await stack.enter_async_context(httpx.AsyncClient()),
                download_chunk_size=chunk_size,
                stream=stream,
            )
        case MediaSource.PATH:
            assert isinstance(media, (str, pathlib.Path))
            return get_media_from_path(stack, path=media)
        case MediaSource.BYTES:
            assert isinstance(media, (bytes, bytearray, memoryview))
            content = bytes(media)
            return MediaInfo(content, None, None, len(content))
        case MediaSource.FILE_OBJ:
            return get_media_from_file_like_obj(file_obj=cast(BinaryIO, media))
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            assert isinstance(media, (str, Media))
            return await get_media_from_media_id_or_obj_or_url(
                stack,
                wa=wa,
                media=media,
                media_source=source,
                download_chunk_size=chunk_size,
                stream=stream,
            )
        case MediaSource.BYTES_GEN:
            # a sync generator may block while producing chunks: never on the event loop
            content = await asyncio.to_thread(b"".join, cast("Iterator[bytes]", media))
            return MediaInfo(content, None, None, len(content))
        case MediaSource.ASYNC_BYTES_GEN:
            content = b"".join(
                [chunk async for chunk in cast("AsyncIterator[bytes]", media)]
            )
            return MediaInfo(content, None, None, len(content))
        case MediaSource.BASE64_DATA_URI | MediaSource.BASE64:
            assert isinstance(media, str)
            return get_media_from_base64(base64_str=media)
    raise ValueError(
        "Media source must be URL, file path, bytes, bytes generator, file-like object, WhatsApp Media, or base64 string."
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
    Internal method to upload media to WhatsApp servers. Returns the uploaded ``Media``.
    """
    async with contextlib.AsyncExitStack() as stack:
        media_info = await open_media(
            stack,
            wa=wa,
            media=media,
            source=media_source,
            stream=False,
            dl_session=dl_session,
        )
        final_filename, final_mimetype = resolve_media_name_and_type(
            media_info=media_info,
            filename=filename,
            mime_type=mime_type,
            media_type=media_type,
        )
        logger.debug(
            "Uploading media to WhatsApp servers: filename=%s, mime_type=%s, length=%s",
            final_filename,
            final_mimetype,
            media_info.length,
        )
        uploaded = _AsyncMedia(
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
        logger.info(
            "Uploaded media %s (%s, %s bytes) -> %s",
            final_filename,
            final_mimetype,
            media_info.length,
            uploaded.id,
        )
        return uploaded


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
            for example, comps in group_by_media(not_uploaded, lambda x: x._example)
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
    source = detect_media_source(file)
    if source == MediaSource.FILE_HANDLE:
        return str(file), source

    try:
        async with contextlib.AsyncExitStack() as stack:
            media_info = await open_media(
                stack, wa=wa, media=file, source=source, stream=True
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
            content = media_info.content
            if source in (MediaSource.PATH, MediaSource.FILE_OBJ):
                # httpx's async client can't send a blocking file object
                content = aiter_file(cast(BinaryIO, content), DOWNLOAD_CHUNK_SIZE)
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
                    file=cast("bytes | AsyncIterator[bytes] | BinaryIO", content),
                    file_offset=0,
                    content_length=media_info.length,
                )
            )["h"], source

    except WhatsAppError:
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to upload media for file upload with file: {describe_media(file)}: {e}"
        ) from e


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
        handle, _ = await internal_upload_file(
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
        for comp in comps:
            comp._set_uploaded(handle)

    except WhatsAppError:
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {describe_media(example)}: {e}"
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
            for media, params in group_by_media(not_uploaded, lambda x: x.media)
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
    except WhatsAppError:
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to upload media for parameter {first_param} with media: {describe_media(media)}: {e}"
        ) from e
