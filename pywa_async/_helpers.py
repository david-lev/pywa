from __future__ import annotations

import asyncio
import itertools
import mimetypes
from contextlib import _AsyncGeneratorContextManager

import httpx

from pywa._helpers import *  # noqa: F403

import pathlib

from pywa._helpers import (
    _media_types_default_filenames,
    _template_header_formats_filename,
    _template_header_formats_default_mime_types,
    _media_types_default_mime_types,
    detect_media_source,
    MediaSource,
    get_media_from_path,
    MediaInfo,
    get_media_from_file_like_obj,
    _filter_not_uploaded_comps,
    _filter_not_uploaded_params,
    _header_format_to_media_type,
    get_filename_from_httpx_response_headers,
    DOWNLOAD_CHUNK_SIZE,
    GeneratorStreamer,
    get_media_from_base64,
)
from pywa.types.templates import (
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    _BaseMediaParams,
    BaseParams,
)

from typing import BinaryIO, Literal, TYPE_CHECKING, Coroutine, Iterator, AsyncIterator

from .types.media import Media

if TYPE_CHECKING:
    from pywa_async import WhatsApp


async def resolve_media_param(
    *,
    wa: WhatsApp,
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
    media_type: Literal["image", "video", "audio", "sticker", "document"] | None,
    phone_id: str,
) -> tuple[bool, bool, str | Media, str]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``uploaded``, ``media/id/url``, ``filename``).
    """
    source = detect_media_source(media)
    match source:
        case MediaSource.EXTERNAL_URL:
            return True, False, str(media), filename or pathlib.Path(media).name
        case MediaSource.MEDIA_ID:
            return False, False, str(media), filename
        case MediaSource.MEDIA_OBJ:
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
    wa: WhatsApp,
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
            url, mime_type = (
                await media.get_media_url(),
                getattr(media, "mime_type", None),
            )
        case MediaSource.MEDIA_URL:
            url, mime_type = media, None
        case _:
            raise ValueError(
                "media must be MediaSource.MEDIA_ID, MEDIA_OBJ or MEDIA_URL"
            )
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
    wa: WhatsApp,
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
                (dl_session, False) if dl_session else (httpx.AsyncClient(), True)
            )
            media_info = await get_media_from_url(
                url=media,
                dl_session=client,
                download_chunk_size=None,
                stream=False,
            )
        case MediaSource.PATH:
            media_info = get_media_from_path(path=media)
        case MediaSource.BYTES:
            media_info = MediaInfo(
                content=media, filename=None, mime_type=None, length=len(media)
            )
        case MediaSource.FILE_OBJ:
            media_info = get_media_from_file_like_obj(file_obj=media)
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            media_info = await get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=media,
                media_source=media_source,
                download_chunk_size=None,
                stream=False,
            )
        case MediaSource.BYTES_GEN:
            media_info = MediaInfo(
                content=GeneratorStreamer(media),
                filename=None,
                mime_type=None,
                length=None,
            )
        case MediaSource.ASYNC_BYTES_GEN:
            content = b"".join([chunk async for chunk in media])
            media_info = MediaInfo(
                content=content,
                filename=None,
                mime_type=None,
                length=len(content),
            )
        case MediaSource.BASE64_DATA_URI, MediaSource.BASE64:
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
        or _media_types_default_filenames.get(media_type, "file.txt")
    )
    try:
        return Media(
            _client=wa,
            _id=(
                await wa.api.upload_media(
                    phone_id=phone_id,
                    media=media_info.content,
                    mime_type=mime_type
                    or media_info.mime_type
                    or _media_types_default_mime_types.get(media_type, "text/plain"),
                    filename=final_filename,
                )
            )["id"],
            uploaded_to=phone_id,
            filename=final_filename,
        )
    finally:
        try:
            if close_client:
                await client.aclose()
            if media_source == MediaSource.PATH:
                media_info.content.close()
        except Exception:
            pass


async def upload_template_media_components(
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
    except Exception as e:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise e


async def internal_upload_file(
    *,
    wa: WhatsApp,
    file: str
    | int
    | Media
    | pathlib.Path
    | bytes
    | BinaryIO
    | Iterator[bytes]
    | AsyncIterator[bytes],
    app_id: int | str,
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
                url=file,
                dl_session=client,
                download_chunk_size=DOWNLOAD_CHUNK_SIZE,
                stream=True,
            )
        case MediaSource.PATH:
            p = pathlib.Path(file)
            with p.open("rb") as f:
                media_info = MediaInfo(
                    content=f.read(),
                    filename=p.name,
                    mime_type=mimetypes.guess_type(p.as_posix())[0],
                    length=p.stat().st_size,
                )
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            media_info = await get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=file,
                media_source=source,
                download_chunk_size=DOWNLOAD_CHUNK_SIZE,
                stream=True,
            )
        case MediaSource.BYTES:
            media_info = MediaInfo(
                content=file, filename=None, mime_type=None, length=len(file)
            )
        case MediaSource.FILE_OBJ:
            media_info = get_media_from_file_like_obj(file)
        case MediaSource.BYTES_GEN:
            all_bytes = b"".join(file)
            media_info = MediaInfo(
                content=all_bytes,
                filename=None,
                mime_type=None,
                length=len(all_bytes),
            )
        case MediaSource.ASYNC_BYTES_GEN:
            all_bytes = b"".join([chunk async for chunk in file])
            media_info = MediaInfo(
                content=all_bytes,
                filename=None,
                mime_type=None,
                length=len(all_bytes),
            )
        case MediaSource.BASE64_DATA_URI | MediaSource.BASE64:
            media_info = get_media_from_base64(base64_str=file)
        case MediaSource.FILE_HANDLE:
            return file, source

    try:
        if not media_info:
            raise ValueError(
                f"Invalid media example for file upload: {file}. "
                "It must be a URL, file path, bytes, file-like object, WhatsApp Media, or file handle."
            )
        if media_info.length is None:
            raise ValueError("Media must have a known length.")

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
                        file_name=media_info.filename or fallback_filename,
                        file_length=media_info.length,
                        file_type=mime_type
                        or media_info.mime_type
                        or fallback_mime_type,
                    )
                )["id"],
                file=media_info.content,
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
        except Exception:
            pass


async def _upload_comps_example(
    *,
    wa: WhatsApp,
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
            fallback_mime_type=_template_header_formats_default_mime_types.get(
                first_comp.format, "application/octet-stream"
            ),
            fallback_filename=_template_header_formats_filename.get(
                first_comp.format, "pywa-template-header"
            ),
        )
        is_media_obj = source == MediaSource.MEDIA_OBJ
        is_open_file = source == MediaSource.FILE_OBJ
        for comp in comps:
            comp._handle = handle
            if is_media_obj:
                comp._example = (
                    comp._example.id
                )  # prevent keeping Media obj in _example
            if is_open_file:
                try:
                    comp._example = (
                        comp._example.name
                    )  # prevent keeping file obj in _example
                except AttributeError:
                    pass

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {example if not isinstance(example, bytes) else '<bytes>'}: {e}"
        ) from e


async def upload_template_media_params(
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
    wa: WhatsApp,
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
            media_type=_header_format_to_media_type[first_param.format],
            phone_id=sender,
        )
        for p in params:
            p._is_url = is_url
            p._resolved_media = uploaded_media.id if uploaded else None
            p._fallback_filename = fallback_filename
    except Exception as e:
        raise ValueError(
            f"Failed to upload media for parameter {first_param} with media: {media if not isinstance(media, bytes) else '<bytes>'}: {e}"
        ) from e
