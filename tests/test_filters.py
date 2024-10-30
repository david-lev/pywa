import dataclasses
import random
from typing import Callable, TypeVar, cast

import pytest

from pywa import filters as fil
from pywa.errors import WhatsAppError, MediaUploadError
from pywa.filters import Filter
from pywa.types import (
    Message,
    CallbackSelection,
    CallbackButton,
    MessageStatus,
    ReplyToMessage,
    ReferredProduct,
)
from pywa.types.base_update import BaseUpdate
from tests.common import API_VERSIONS, CLIENTS

_T = TypeVar("_T", bound=BaseUpdate)
WHATSAPP_N = "1234567890"


def same(x: _T) -> _T:
    return x


# {filename: {test_name: [(update_modifier, filter_func)]}}

FILTERS: dict[str, dict[str, list[tuple[Callable[[_T], _T], Filter]]]] = {
    "message": {
        "text": [
            (same, fil.text),
            (lambda m: modify_text(m, "hello"), fil.matches("hello")),
            (
                lambda m: modify_text(m, "hello"),
                fil.matches("hello", ignore_case=True),
            ),
            (lambda m: modify_text(m, "hi hello"), fil.contains("hello")),
            (
                lambda m: modify_text(m, "hi Hello"),
                fil.contains("hello", "Hi", ignore_case=True),
            ),
            (
                lambda m: modify_text(m, "hi bye"),
                fil.startswith("hi"),
            ),
            (
                lambda m: modify_text(m, "hi bye"),
                fil.startswith("Hi", ignore_case=True),
            ),
            (
                lambda m: modify_text(m, "hi bye"),
                fil.endswith("bye"),
            ),
            (
                lambda m: modify_text(m, "hi bye"),
                fil.endswith("Bye", ignore_case=True),
            ),
            (
                lambda m: modify_text(m, "hi bye"),
                fil.regex(r"^hi", r"bye$"),
            ),
            (
                lambda m: modify_text(m, "!start"),
                fil.command("start"),
            ),
            (
                lambda m: modify_text(m, "/start"),
                fil.command("start", prefixes="!/"),
            ),
            (
                lambda m: modify_text(m, "!Start"),
                fil.command("staRt", ignore_case=True),
            ),
            (
                lambda m: modify_text(m, "!start"),
                fil.is_command,
            ),
        ],
        "image": [
            (same, fil.image),
            (lambda m: add_caption(m, "caption"), fil.has_caption),
            (
                lambda m: modify_img_mime_type(m, "image/jpeg"),
                fil.mimetypes("image/jpeg"),
            ),
            (
                lambda m: modify_img_mime_type(m, "application/pdf"),
                fil.mimetypes("application/pdf"),
            ),
        ],
        "video": [
            (same, fil.video),
        ],
        "document": [
            (same, fil.document),
        ],
        "audio": [
            (same, fil.audio),
            (same, fil.audio_only),
        ],
        "voice": [
            (same, fil.voice),
        ],
        "sticker": [
            (same, fil.sticker),
        ],
        "static_sticker": [
            (same, fil.static_sticker),
        ],
        "animated_sticker": [
            (same, fil.animated_sticker),
        ],
        "reaction": [
            (same, fil.reaction_added),
            (
                lambda m: modify_reaction(m, "😀"),
                fil.reaction_emojis("😀"),
            ),
        ],
        "unreaction_empty": [
            (same, fil.reaction_removed),
        ],
        "unreaction_no_emoji": [(same, fil.reaction_removed)],
        "current_location": [
            (same, fil.current_location),
            (
                lambda m: modify_location(m, 37.4611794, -122.2531785),
                fil.location_in_radius(37.47, -122.25, 10),
            ),
        ],
        "contacts": [
            (same, fil.contacts),
            (
                lambda m: add_wa_number_to_contact(m),
                fil.contacts_has_wa,
            ),
        ],
        "order": [
            (same, fil.order),
        ],
        "unsupported": [(same, fil.unsupported)],
        "reply": [(same, fil.reply)],
        "replays_to": [(lambda m: modify_replies_to(m, "123"), fil.replays_to("123"))],
        "sent_to": [
            (lambda m: modify_send_to(m, "123"), fil.sent_to(phone_number_id="123"))
        ],
        "sent_to_me": [
            (lambda m: modify_send_to(m, CLIENTS.keys()[0].phone_id), fil.sent_to_me)
        ],
        "from_users": [(lambda m: modify_send_from(m, "123"), fil.from_users("123"))],
        "from_countries": [
            (lambda m: modify_send_from(m, "97212345678"), fil.from_countries("972"))
        ],
        "has_referred_product": [
            (lambda m: modify_referred_product(m, "IPHONE"), fil.has_referred_product)
        ],
        "forwarded": [(same, fil.forwarded)],
        "forwarded_many_times": [(same, fil.forwarded)],
        "interactive_message_with_err": [],
    },
    "callback_button": {
        "button": [
            (
                lambda m: modify_callback_data(m, "hi"),
                fil.matches("hi"),
            ),
            (
                lambda m: modify_callback_data(m, "Hi"),
                fil.matches("hi", ignore_case=True),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.contains("hi"),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.contains("Hi", ignore_case=True),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.startswith("hi"),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.startswith("Hi", ignore_case=True),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.endswith("bye"),
            ),
            (
                lambda m: modify_callback_data(m, "hi bye"),
                fil.endswith("Bye", ignore_case=True),
            ),
            (
                lambda m: modify_callback_data(m, "data:123"),
                fil.regex("^data:", r"\d{3}$"),
            ),
        ],
        "quick_reply": [],
    },
    "callback_selection": {
        "callback": [],
        "description": [],
    },
    "message_status": {
        "sent": [(same, fil.sent)],
        "delivered": [(same, fil.delivered)],
        "read": [(same, fil.read)],
        "failed": [
            (
                lambda m: modify_status_err(
                    m, WhatsAppError.from_dict({"code": 131053, "message": "error"})
                ),
                fil.failed_with(MediaUploadError),
            ),
            (
                lambda m: modify_status_err(
                    m, WhatsAppError.from_dict({"code": 131053, "message": "error"})
                ),
                fil.failed_with(131053),
            ),
        ],
        "with_tracker": [
            (same, fil.with_tracker),
            (lambda s: modify_status_tracker(s, "tracker"), fil.matches("tracker")),
        ],
    },
    "template_status": {
        "approved": [(same, fil.template_status)],
    },
    "flow_completion": {
        "completion": [
            (same, fil.flow_completion),
        ]
    },
    "chat_opened": {"chat_opened": [(same, fil.chat_opened)]},
}

RANDOM_API_VER = random.choice(API_VERSIONS)


def test_combinations():
    true, false = fil.new(lambda _, __: True), fil.new(lambda _, __: False)
    assert true.check_sync(None, None)
    assert not false.check_sync(None, None)
    assert (true & true).check_sync(None, None)
    assert not (true & false).check_sync(None, None)
    assert (true | false).check_sync(None, None)
    assert not (false | false).check_sync(None, None)


@pytest.mark.asyncio
async def test_combinations_async():
    async def _async_true(_, __):
        return True

    async def _async_false(_, __):
        return False

    async_true, async_false = fil.new(_async_true), fil.new(_async_false)
    sync_true, sync_false = fil.new(lambda _, __: True), fil.new(lambda _, __: False)

    assert await async_true.check_async(None, None)
    assert not await async_false.check_async(None, None)
    assert await (async_true & async_true).check_async(None, None)
    assert await (sync_true & async_true).check_async(None, None)
    assert await (async_true & sync_true).check_async(None, None)
    assert not await (async_true & async_false).check_async(None, None)
    assert not await (sync_true & async_false).check_async(None, None)
    assert await (async_true | async_false).check_async(None, None)
    assert await (sync_true | async_false).check_async(None, None)
    assert await (async_false | sync_true).check_async(None, None)
    assert not await (async_false | async_false).check_async(None, None)
    assert not await (sync_false | sync_false).check_async(None, None)


def test_filters():
    for client, updates in CLIENTS.items():
        for filename, tests in updates[RANDOM_API_VER].items():
            for test in tests:
                for test_name, update in test.items():
                    for update_modifier, filter_obj in FILTERS.get(filename, {}).get(
                        test_name, ()
                    ):
                        update = update_modifier(update)
                        try:
                            assert cast(Filter, filter_obj).check_sync(client, update)
                        except AssertionError as e:
                            raise AssertionError(
                                f"Test {filename}/{test_name} failed on {update}"
                            ) from e


def modify_text(msg: Message, to: str):
    return dataclasses.replace(msg, text=to)


def add_caption(msg: Message, caption: str):
    return dataclasses.replace(msg, caption=caption)


def modify_img_mime_type(msg: Message, mime_type: str):
    return dataclasses.replace(
        msg, image=dataclasses.replace(msg.image, mime_type=mime_type)
    )


def modify_reaction(msg: Message, emoji: str | None):
    return dataclasses.replace(
        msg, reaction=dataclasses.replace(msg.reaction, emoji=emoji)
    )


def modify_location(msg: Message, lat: float, lon: float):
    return dataclasses.replace(
        msg, location=dataclasses.replace(msg.location, latitude=lat, longitude=lon)
    )


def add_wa_number_to_contact(msg: Message):
    return dataclasses.replace(
        msg,
        contacts=(
            dataclasses.replace(
                msg.contacts[0],
                phones=[
                    dataclasses.replace(msg.contacts[0].phones[0], wa_id="123456789")
                ],
            ),
        ),
    )


def modify_callback_data(clb: CallbackButton | CallbackSelection, data: str):
    return dataclasses.replace(clb, data=data)


def modify_status_err(status: MessageStatus, err: WhatsAppError):
    return dataclasses.replace(status, error=err)


def modify_send_from(msg: Message, wa_id: str):
    return dataclasses.replace(
        msg, from_user=dataclasses.replace(msg.from_user, wa_id=wa_id)
    )


def modify_send_to(msg: Message, wa_id: str):
    return dataclasses.replace(
        msg, metadata=dataclasses.replace(msg.metadata, phone_number_id=wa_id)
    )


def modify_replies_to(msg: Message, message_id: str):
    return dataclasses.replace(
        msg,
        reply_to_message=dataclasses.replace(
            msg.reply_to_message, message_id=message_id
        ),
    )


def modify_referred_product(msg: Message, product: str):
    reply_to_msg = ReplyToMessage(
        message_id=msg.id,
        from_user_id=msg.from_user.wa_id,
        referred_product=ReferredProduct(catalog_id="123", sku=product),
    )
    return dataclasses.replace(msg, reply_to_message=reply_to_msg)


def modify_status_tracker(s: MessageStatus, tracker: str):
    return dataclasses.replace(s, tracker=tracker)
