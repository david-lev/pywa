import dataclasses
import datetime
import functools
from types import ModuleType

from pywa import handlers, types, WhatsApp, filters
from pywa.handlers import MessageHandler
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


def test_decorators():
    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message(filters=filters.text)
    def instance_with_parentheses(_, __): ...

    assert wa._handlers[MessageHandler][0]._callback == instance_with_parentheses

    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message
    def instance_without_parentheses(_, __): ...

    assert wa._handlers[MessageHandler][0]._callback == instance_without_parentheses

    module = ModuleType("module")

    @WhatsApp.on_message(filters=filters.text)
    def class_with_parentheses(_, __): ...

    module.__dict__["on_message"] = class_with_parentheses
    wa = WhatsApp(server=None, verify_token="1234567890", handlers_modules=[module])
    assert wa._handlers[MessageHandler][0]._callback == class_with_parentheses

    module = ModuleType("module")

    @WhatsApp.on_message
    def class_without_parentheses(_, __): ...

    module.__dict__["on_message"] = class_without_parentheses
    wa = WhatsApp(server=None, verify_token="1234567890", handlers_modules=[module])
    assert wa._handlers[MessageHandler][0]._callback == class_without_parentheses

    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message(filters=filters.text)
    @wa.on_message
    @WhatsApp.on_message(filters=filters.text)
    @WhatsApp.on_message
    def all_combinations(_, __): ...

    module = ModuleType("module")
    module.__dict__["on_message"] = all_combinations
    wa.load_handlers_modules(module)
    assert len(wa._handlers[MessageHandler]) == 4
