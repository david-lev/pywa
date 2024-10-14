import dataclasses
import datetime
import functools

from pywa import handlers, types, WhatsApp, filters
from pywa_async import WhatsApp as WhatsAppAsync

FAKE_WA = WhatsApp(phone_id="1234567890", token="1234567890:1234567890")
FAKE_WA_ASYNC = WhatsAppAsync(phone_id="1234567890", token="1234567890:1234567890")


CallbackButtonOnlyDataIsNeeded = functools.partial(
    types.CallbackButton,
    _client=FAKE_WA,
    raw={},
    id="123",
    type=types.MessageType.INTERACTIVE,
    metadata=types.Metadata(
        display_phone_number="1234567890",
        phone_number_id="1234567890",
    ),
    from_user=types.User(
        wa_id="1234567890",
        name="John",
    ),
    timestamp=datetime.datetime.now(),
    reply_to_message=types.ReplyToMessage(
        message_id="123",
        from_user_id="1234567890",
        referred_product=None,
    ),
    title="Click me",
)


def test_all_updates_are_overridden():
    assert (
        FAKE_WA._handlers_to_update_constractor.keys()
        == FAKE_WA_ASYNC._handlers_to_update_constractor.keys()
    )


def test_resolve_factory_callback_data_subclass():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    callback_data = User(id=1, name="John")
    constructor, factory_filter = handlers._resolve_factory(User, "data")
    button_data = types.Button(title="Click me", callback_data=callback_data).to_dict()[
        "reply"
    ]["id"]
    constructed_data = constructor(button_data)
    assert constructed_data == callback_data

    update = CallbackButtonOnlyDataIsNeeded(data=button_data)
    assert factory_filter(FAKE_WA, update)
