import json
from typing import Any

from pywa import WhatsApp
from pywa.types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    TemplateStatus,
)
from pywa.types.base_update import BaseUpdate

API_VERSIONS: list[float] = [18.0]

UPDATES: dict[tuple[str, type[BaseUpdate]], list[str]] = {
    ("message", Message): [
        "text",
        "image",
        "video",
        "document",
        "audio",
        "voice",
        "static_sticker",
        "animated_sticker",
        "location",
        "contacts",
        "order",
        "unsupported",
        "reply",
        "forwarded",
        "forwarded_many_times",
    ],
    ("callback_button", CallbackButton): [
        "button",
        "quick_reply",
    ],
    ("callback_selection", CallbackSelection): [
        "callback",
        "description",
    ],
    ("message_status", MessageStatus): [
        "sent",
        "failed",
    ],
    ("template_status", TemplateStatus): [
        "approved",
    ],
}


def test_types():
    client = WhatsApp(phone_id="1234567890", token="xyzxyzxyz")
    for version in API_VERSIONS:
        for (update_id, update_type), updates in UPDATES.items():
            with open(f"tests/data/{version}/{update_id}.json", "r") as update_file:
                update_data: dict[str, Any] = json.load(update_file)
                for update in updates:
                    try:
                        update = update_type.from_update(
                            client=client, update=update_data[update]
                        )  # noqa
                    except Exception as e:
                        raise AssertionError(
                            f"Failed to parse update '{update_id}': test='{update}', v={version}, error={e}"
                        )
