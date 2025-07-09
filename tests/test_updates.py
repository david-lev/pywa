from typing import Any, Callable

from pywa.types import (
    MessageType,
    MessageStatusType,
    TemplateStatusUpdate,
)
from pywa.types.calls import CallEvent
from pywa.types.media import Image, Video, Document, Audio
from .common import CLIENTS

# {update_file: {update_name: [test_funcs]}}
TESTS: dict[str, dict[str, list[Callable[[Any], bool]]]] = {
    "message": {
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
        "current_location": [lambda m: m.location.current_location],
        "chosen_location": [lambda m: not m.location.current_location],
        "contacts": [lambda m: m.contacts is not None],
        "order": [lambda m: m.order is not None],
        "system": [lambda m: m.system is not None],
        "unsupported": [lambda m: m.error is not None],
        "reply": [lambda m: m.is_reply],
        "forwarded": [lambda m: m.forwarded],
        "forwarded_many_times": [lambda m: m.forwarded_many_times],
        "interactive_message_with_err": [
            lambda m: m.type == MessageType.INTERACTIVE and m.error is not None
        ],
    },
    "callback_button": {
        "button": [lambda b: b.type == MessageType.INTERACTIVE],
        "quick_reply": [lambda b: b.type == MessageType.BUTTON],
    },
    "callback_selection": {
        "callback": [lambda s: s.data is not None],
        "description": [lambda s: s.description is not None],
    },
    "message_status": {
        "sent": [lambda s: s.status == MessageStatusType.SENT],
        "delivered": [lambda s: s.status == MessageStatusType.DELIVERED],
        "read": [lambda s: s.status == MessageStatusType.READ],
        "failed": [lambda s: s.error is not None],
        "with_tracker": [lambda s: s.tracker is not None],
    },
    # "template_status": {
    #     "approved": [lambda s: s.event == TemplateStatus.TemplateEvent.APPROVED],
    # },
    "flow_completion": {
        "completion": [
            lambda f: f.token is not None,
            lambda f: "flow_token" not in f.response,
        ],
        "without_flow_token": [lambda f: f.token is None],
    },
    "chat_opened": {
        "chat_opened": [lambda c: c.type == MessageType.REQUEST_WELCOME],
    },
    "call_connect": {
        "call_connect": [lambda c: c.event == CallEvent.CONNECT],
    },
    "call_terminate": {
        "call_terminate": [lambda c: c.event == CallEvent.TERMINATE],
    },
    "call_status": {
        "call_status": [lambda c: c.type is not None],
    },
    "user_preferences": {
        "user_preferences": [lambda u: u.value is not None],
        "user_marketing_preferences": [
            lambda u: u.value in ["stop", "resume"]
            and u.category == "marketing_messages"
        ],
    },
}


def test_types():
    for client, update_files in CLIENTS.items():
        for file, updates in update_files.items():
            for update_name, update in updates.items():
                for test_func in TESTS[file.stem][update_name]:
                    try:
                        assert test_func(update)
                    except AssertionError as e:
                        raise AssertionError(
                            f"Failed to assert update_name='{update_name}' error={e}"
                        )
