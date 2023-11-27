import json
from typing import Any, TypeVar, Callable

from pywa import WhatsApp
from pywa.types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    TemplateStatus,
    MessageType,
    MessageStatusType,
)
from pywa.types.base_update import BaseUpdate
from pywa.types.media import Image, Video, Document, Audio

API_VERSIONS: list[float] = [18.0]
T = TypeVar("T", bound=BaseUpdate)

UPDATES: dict[tuple[str, type[T]], dict[str, list[Callable[[T], bool]]]] = {
    ("message", Message): {
        "text": [lambda m: m.text is not None],
        "image": [
            lambda m: m.image is not None,
            lambda m: m.has_media,
            lambda m: isinstance(m.media, Image),
        ],
        "video": [
            lambda m: m.video is not None,
            lambda m: m.has_media,
            lambda m: isinstance(m.media, Video),
        ],
        "document": [
            lambda m: m.document is not None,
            lambda m: m.has_media,
            lambda m: isinstance(m.media, Document),
        ],
        "audio": [
            lambda m: not m.audio.voice,
            lambda m: m.has_media,
            lambda m: isinstance(m.media, Audio),
        ],
        "voice": [lambda m: m.audio.voice],
        "static_sticker": [lambda m: not m.sticker.animated],
        "animated_sticker": [lambda m: m.sticker.animated],
        "reaction": [
            lambda m: m.reaction.emoji is not None,
            lambda m: m.id != m.message_id_to_reply,
        ],
        "unreaction_empty": [lambda m: m.reaction.emoji is None],
        "unreaction_no_emoji": [lambda m: m.reaction.emoji is None],
        "location": [lambda m: m.location is not None],
        "contacts": [lambda m: m.contacts is not None],
        "order": [lambda m: m.order is not None],
        "unsupported": [lambda m: m.error is not None],
        "reply": [lambda m: m.is_reply],
        "forwarded": [lambda m: m.forwarded],
        "forwarded_many_times": [lambda m: m.forwarded_many_times],
        "interactive_message_with_err": [
            lambda m: m.type == MessageType.INTERACTIVE and m.error is not None
        ],
    },
    ("callback_button", CallbackButton): {
        "button": [lambda b: b.type == MessageType.INTERACTIVE],
        "quick_reply": [lambda b: b.type == MessageType.BUTTON],
    },
    ("callback_selection", CallbackSelection): {
        "callback": [lambda s: s.data is not None],
        "description": [lambda s: s.description is not None],
    },
    ("message_status", MessageStatus): {
        "sent": [lambda s: s.status == MessageStatusType.SENT],
        "failed": [lambda s: s.error is not None],
    },
    ("template_status", TemplateStatus): {
        "approved": [lambda s: s.event == TemplateStatus.TemplateEvent.APPROVED],
    },
}


def test_types():
    client = WhatsApp(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False)
    for version in API_VERSIONS:
        for (update_filename, update_class), examples in UPDATES.items():
            with open(
                f"tests/data/{version}/{update_filename}.json", "r"
            ) as update_file:
                examples_data: dict[str, Any] = json.load(update_file)
            for test_name, test_funcs in examples.items():
                try:
                    update_dict = examples_data[test_name]
                    handler = client._get_handler(update_dict)
                    assert (
                        handler.__field_name__
                        == update_dict["entry"][0]["changes"][0]["field"]
                    )
                    update_obj = handler.__update_constructor__(client, update_dict)  # noqa
                    assert isinstance(update_obj, update_class)
                    for test_func in test_funcs:
                        assert test_func(update_obj)
                except Exception as e:
                    raise AssertionError(
                        f"Failed to parse update='{update_filename}', test='{test_name}', v={version}, error={e}"
                    )
