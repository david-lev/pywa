from __future__ import annotations

import asyncio
import itertools
import mimetypes

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
    media_id, filename = await internal_upload_media(
        media=media,
        media_source=source,
        media_type=media_type,
        mime_type=mime_type,
        filename=filename,
        wa=wa,
        phone_id=phone_id,
    )
    return False, media_id, filename


async def get_media_from_url(
    url: str,
    dl_session: httpx.AsyncClient,
) -> MediaInfo:
    res = await dl_session.get(url, follow_redirects=True)
    try:
        res.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"An error occurred while downloading from {url}") from e
    return MediaInfo(
        content=res.content,
        filename=get_filename_from_httpx_response_headers(res.headers)
        or pathlib.Path(url).name,
        mime_type=res.headers.get("Content-Type") or mimetypes.guess_type(url)[0],
        length=len(res.content),
    )


async def get_media_from_media_id_or_obj_or_url(
    wa: WhatsApp,
    media: str | Media,
    media_source: MediaSource,
) -> MediaInfo:
    filename: str | None = None
    mime_type: str | None = None
    url: str | None = None
    match media_source:
        case MediaSource.MEDIA_ID:
            url_res = await wa.get_media_url(media_id=str(media))
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_OBJ:
            url_res = await wa.get_media_url(media_id=media.id)
            url, mime_type = url_res.url, url_res.mime_type
        case MediaSource.MEDIA_URL:
            url, mime_type = media, None
    if url is None:
        raise ValueError("Failed to resolve media URL")

    async with wa.api.stream_media_bytes(media_url=url) as res:
        try:
            res.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"An error occurred while downloading from {url}") from e

    return MediaInfo(
        content=await res.aread(),
        filename=filename or get_filename_from_httpx_response_headers(res.headers),
        mime_type=mime_type or res.headers.get("Content-Type"),
        length=int(res.headers.get("Content-Length", "0")) or None,
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
) -> tuple[str, str]:
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
        return (
            await wa.api.upload_media(
                phone_id=phone_id,
                media=media_info.content,
                mime_type=mime_type
                or media_info.mime_type
                or _media_types_default_mime_types.get(media_type, "text/plain"),
                filename=final_filename,
            )
        )["id"], final_filename
    finally:
        try:  # close file or stream
            if close_client:
                client.close()  # type: ignore
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
                not_uploaded, key=lambda x: x.example
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
    media_info: MediaInfo | None = None
    client = None

    source = detect_media_source(example)
    match source:
        case MediaSource.EXTERNAL_URL:
            client = httpx.AsyncClient()
            media_info = await get_media_from_url(
                url=example,
                dl_session=client,
            )
        case MediaSource.PATH:
            media_info = get_media_from_path(path=example)
        case MediaSource.MEDIA_ID | MediaSource.MEDIA_OBJ | MediaSource.MEDIA_URL:
            media_info = await get_media_from_media_id_or_obj_or_url(
                wa=wa,
                media=example,
                media_source=source,
            )
        case MediaSource.BYTES:
            media_info = MediaInfo(
                content=example, filename=None, mime_type=None, length=len(example)
            )
        case MediaSource.FILE_OBJ:
            media_info = get_media_from_file_like_obj(example)
        case MediaSource.BYTES_GEN:
            all_bytes = b"".join(example)
            media_info = MediaInfo(
                content=all_bytes,
                filename=None,
                mime_type=None,
                length=len(all_bytes),
            )
        case MediaSource.ASYNC_BYTES_GEN:
            all_bytes = b"".join([chunk async for chunk in example])
            media_info = MediaInfo(
                content=all_bytes,
                filename=None,
                mime_type=None,
                length=len(all_bytes),
            )
        case MediaSource.BASE64_DATA_URI | MediaSource.BASE64:
            media_info = get_media_from_base64(base64_str=example)
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
        handle = (
            await wa.api.upload_file(
                upload_session_id=(
                    await wa.api.create_upload_session(
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
                    )
                )["id"],
                file=media_info.content,
                file_offset=0,
            )
        )["h"]

        for comp in comps:
            comp._handle = handle

    except Exception as e:
        raise ValueError(
            f"Failed to upload media for component {first_comp.__class__.__name__} with example: {example if not isinstance(example, bytes) else '<bytes>'}"
        ) from e

    finally:
        if client:
            await client.aclose()


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
        is_url, media_id_or_url, fallback_filename = await resolve_media_param(
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
