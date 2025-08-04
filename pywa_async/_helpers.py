from __future__ import annotations

import asyncio
import mimetypes

import httpx

from pywa._helpers import *  # noqa: F403

import pathlib

from pywa._helpers import (
    _media_types_default_filenames,
    _template_header_formats_filename,
    _template_header_formats_default_mime_types,
)
from pywa.types.templates import (
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    Carousel,
    _BaseMediaParams,
)
from .types import MessageType

from typing import BinaryIO, Literal, TYPE_CHECKING

from .types.media import Media

if TYPE_CHECKING:
    from pywa_async import WhatsApp


async def resolve_media_param(
    wa: WhatsApp,
    media: str | Media | pathlib.Path | bytes | BinaryIO,
    mime_type: str | None,
    filename: str | None,
    media_type: Literal[
        MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.STICKER
    ]
    | None,
    phone_id: str,
) -> tuple[bool, str]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``media_id_or_url``).
    """
    if isinstance(media, Media):
        return False, media.id
    if isinstance(media, (str, pathlib.Path)):
        if str(media).startswith(("https://", "http://")):
            return True, media
        elif str(media).isdigit() and not pathlib.Path(media).is_file():
            return False, media  # assume it's a media ID
    # assume its bytes or a file path
    return False, (
        await wa.upload_media(
            phone_id=phone_id,
            media=media,
            mime_type=mime_type,
            filename=_media_types_default_filenames.get(media_type, filename),
        )
    ).id


async def upload_template_media_components(
    *,
    wa: WhatsApp,
    app_id: int | str | None,
    components: list[TemplateBaseComponent | dict],
) -> None:
    """
    Internal method to upload media components examples in a template.
    """
    not_uploaded = []
    for comp in components:
        if isinstance(comp, _BaseMediaHeaderComponent) and comp._handle is None:
            not_uploaded.append(comp)
        elif isinstance(comp, Carousel):
            for card in comp.cards:
                for cc in card.components:
                    if isinstance(cc, _BaseMediaHeaderComponent) and cc._handle is None:
                        not_uploaded.append(cc)
    if not_uploaded:
        await _run_all_and_cancel_on_exception(
            *[
                _upload_comp(
                    wa=wa,
                    c=c,
                    app_id=app_id,
                )
                for c in not_uploaded
            ]
        )


async def _run_all_and_cancel_on_exception(*coros):
    tasks = [asyncio.create_task(c) for c in coros]

    try:
        return await asyncio.gather(*tasks)
    except Exception as e:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise e


async def _upload_comp(
    *, wa: WhatsApp, c: _BaseMediaHeaderComponent, app_id: int | str | None
) -> None:
    example = c.example
    filename: str | None = None
    mime_type: str | None = None
    raw_bytes: bytes | None = None
    try:
        if isinstance(example, (str, pathlib.Path, Media)):
            if str(example).startswith(("https://", "http://")):  # URL
                res = await httpx.AsyncClient(follow_redirects=True).get(str(example))
                res.raise_for_status()
                raw_bytes = res.content
                mime_type = res.headers.get("Content-Type")
            elif (path := pathlib.Path(example)).is_file():  # File path
                with open(path, "rb") as f:
                    filename = path.name
                    mime_type = mimetypes.guess_type(path)[0]
                    raw_bytes = f.read()
            elif str(example).isdigit() or isinstance(
                example, Media
            ):  # WhatsApp Media ID
                url_res = await wa.get_media_url(
                    media_id=example.id if isinstance(example, Media) else example
                )
                mime_type = url_res.mime_type
                raw_bytes = await wa.download_media(url=url_res.url, in_memory=True)
        elif isinstance(example, bytes):
            raw_bytes = example
        if not raw_bytes:
            raise ValueError(
                f"Invalid media example for component {c.__class__.__name__}: {example}. "
                "It must be a URL, file path, WhatsApp Media, or bytes."
            )
        app_id = resolve_arg(
            wa=wa,
            value=app_id,
            method_arg="app_id",
            client_arg="app_id",
        )
        c._handle = (
            await wa.api.upload_file(
                upload_session_id=(
                    await wa.api.create_upload_session(
                        app_id=app_id,
                        file_name=filename
                        or _template_header_formats_filename.get(
                            c.format, "pywa-template-header"
                        ),
                        file_length=len(raw_bytes),
                        file_type=mime_type
                        or _template_header_formats_default_mime_types.get(
                            c.format, "application/octet-stream"
                        ),
                    )
                )["id"],
                file=raw_bytes,
                file_offset=0,
            )
        )["h"]
    except Exception as e:
        e.add_note(
            f"Failed to upload media for component {c.__class__.__name__} with example: {example}"
        )
        raise


async def upload_template_media_params(
    *,
    wa: WhatsApp,
    sender: str,
    params: list[TemplateBaseComponent.Params | dict],
) -> None:
    """
    Internal method to upload media parameters when sending a template message.
    """
    not_uploaded = []
    for param in params:
        if isinstance(param, _BaseMediaParams) and param._resolved_media is None:
            not_uploaded.append(param)
        elif isinstance(param, Carousel.Params):
            for card_params in param.cards:
                for p in card_params.params:
                    if isinstance(p, _BaseMediaParams) and p._resolved_media is None:
                        not_uploaded.append(p)

    if not not_uploaded:
        return

    await _run_all_and_cancel_on_exception(
        *[
            _upload_param(
                wa=wa,
                sender=sender,
                p=p,
            )
            for p in not_uploaded
        ]
    )


async def _upload_param(*, wa: WhatsApp, sender: str, p: _BaseMediaParams) -> None:
    try:
        p._is_url, p._resolved_media = await resolve_media_param(
            wa=wa,
            media=p.media,
            mime_type=None,
            filename=None,
            media_type=p.format.value,
            phone_id=sender,
        )
    except Exception as e:
        e.add_note(f"Failed to upload media parameter with media: {p.media}")
        raise e
