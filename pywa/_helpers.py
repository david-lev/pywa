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

import datetime
import json
import mimetypes
import pathlib
import threading
from concurrent import futures
from typing import Any, BinaryIO, Literal, Iterable, TYPE_CHECKING

import httpx

from .types import (
    FlowMetricName,
    FlowMetricGranularity,
    FlowJSON,
    CallbackData,
    MessageType,
    URLButton,
    VoiceCallButton,
    SectionList,
    FlowButton,
    Button,
    CallPermissionRequestButton,
)
from pywa.types.others import InteractiveType
from .types.media import Media
from .types.templates import (
    TemplateBaseComponent,
    _BaseMediaHeaderComponent,
    HeaderFormatType,
    Carousel,
    _BaseMediaParams,
)

if TYPE_CHECKING:
    from pywa import WhatsApp


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
    dict[str, set[str] | str],
]:
    """
    Internal method to resolve ``buttons`` parameter. Returns a tuple of (``type``, ``buttons``, ``callback_options``).
    """
    if isinstance(buttons, SectionList):
        data = buttons.to_dict()
        return (
            InteractiveType.LIST,
            data,
            {
                "_callback_options": {
                    row["id"] for section in data["sections"] for row in section["rows"]
                }
            },
        )
    elif isinstance(buttons, URLButton):
        return InteractiveType.CTA_URL, buttons.to_dict(), {}
    elif isinstance(buttons, VoiceCallButton):
        return InteractiveType.VOICE_CALL, buttons.to_dict(), {}
    elif isinstance(buttons, CallPermissionRequestButton):
        return InteractiveType.CALL_PERMISSION_REQUEST, buttons.to_dict(), {}
    elif isinstance(buttons, FlowButton):
        return (
            InteractiveType.FLOW,
            buttons.to_dict(),
            {"_flow_token": buttons.flow_token},
        )
    else:  # assume its list of buttons
        data = tuple(b.to_dict() for b in buttons)
        return (
            InteractiveType.BUTTON,
            {"buttons": data},
            {"_callback_options": {b["reply"]["id"] for b in data}},
        )


_media_types_default_filenames = {
    "IMAGE": "pywa-image.jpg",
    "VIDEO": "pywa-video.mp4",
    "AUDIO": "pywa-audio.mp3",
    "STICKER": "pywa-sticker.webp",
}
_template_header_formats_filename = {
    HeaderFormatType.IMAGE: "pywa-template-header-image.jpg",
    HeaderFormatType.VIDEO: "pywa-template-header-video.mp4",
    HeaderFormatType.DOCUMENT: "pywa-template-header-document.pdf",
}
_template_header_formats_default_mime_types = {
    HeaderFormatType.IMAGE: "image/jpeg",
    HeaderFormatType.VIDEO: "video/mp4",
    HeaderFormatType.DOCUMENT: "application/pdf",
}


def resolve_media_param(
    wa: WhatsApp,
    media: str | Media | pathlib.Path | bytes | BinaryIO,
    mime_type: str | None,
    filename: str | None,
    media_type: str | None,
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
    return False, wa.upload_media(
        phone_id=phone_id,
        media=media,
        mime_type=mime_type,
        filename=_media_types_default_filenames.get(media_type, filename),
    ).id


def upload_template_media_components(
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
    if not not_uploaded:
        return

    stop_event = threading.Event()
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media"
    ) as executor:
        tasks = [
            executor.submit(
                _upload_comp,
                wa=wa,
                c=c,
                app_id=app_id,
                stop_event=stop_event,
            )
            for c in not_uploaded
        ]
        for future in futures.as_completed(tasks):
            future.result()
            if stop_event.is_set():
                break


def _upload_comp(
    *,
    wa: WhatsApp,
    c: _BaseMediaHeaderComponent,
    app_id: int | str | None,
    stop_event: threading.Event,
) -> None:
    if stop_event.is_set():
        return
    example = c.example
    filename: str | None = None
    mime_type: str | None = None
    raw_bytes: bytes | None = None
    try:
        if isinstance(example, (str, pathlib.Path, Media)):
            if str(example).startswith(("https://", "http://")):  # URL
                res = httpx.Client(follow_redirects=True).get(str(example))
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
                url_res = wa.get_media_url(
                    media_id=example.id if isinstance(example, Media) else example
                )
                mime_type = url_res.mime_type
                raw_bytes = wa.download_media(url=url_res.url, in_memory=True)
        elif isinstance(example, bytes):  # Raw bytes
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
        c._handle = wa.api.upload_file(
            upload_session_id=wa.api.create_upload_session(
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
            )["id"],
            file=raw_bytes,
            file_offset=0,
        )["h"]
    except Exception as e:
        stop_event.set()
        e.add_note(
            f"Failed to upload media for component {c.__class__.__name__} with example: {example}"
        )
        raise


def upload_template_media_params(
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
    with futures.ThreadPoolExecutor(
        thread_name_prefix="pywa-upload-template-media-params"
    ) as executor:
        tasks = [
            executor.submit(
                _upload_param,
                wa=wa,
                sender=sender,
                p=param,
            )
            for param in not_uploaded
        ]
        for task in futures.wait(tasks)[0]:
            task.result()


def _upload_param(*, wa: WhatsApp, sender: str, p: _BaseMediaParams) -> None:
    try:
        p._is_url, p._resolved_media = resolve_media_param(
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
        "type": typ,
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
