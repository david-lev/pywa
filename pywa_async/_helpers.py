from __future__ import annotations

from pywa._helpers import (
    resolve_phone_id_param,
    resolve_tracker_param,
    resolve_waba_id_param,
    resolve_flow_json_param,
    get_interactive_msg,
    get_media_msg,
    get_flow_fields,
    get_flow_metric_field,
    resolve_callback_data,
    resolve_buttons_param,
)

import pathlib

from pywa._helpers import _media_types_default_filenames
from .types import MessageType

from typing import BinaryIO, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from pywa_async import WhatsApp


async def resolve_media_param(
    wa: WhatsApp,
    media: str | pathlib.Path | bytes | BinaryIO,
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
    if isinstance(media, (str, pathlib.Path)):
        if str(media).startswith(("https://", "http://")):
            return True, media
        elif str(media).isdigit() and not pathlib.Path(media).is_file():
            return False, media  # assume it's a media ID
    # assume its bytes or a file path
    return False, await wa.upload_media(
        phone_id=phone_id,
        media=media,
        mime_type=mime_type,
        filename=_media_types_default_filenames.get(media_type, filename),
    )
