import datetime
import functools
from types import ModuleType

import pytest

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


def test_instance_with_parentheses():
    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message(filters=filters.text)  # @wa.on_x(filters=...)
    def instance_with_parentheses(_, __): ...

    assert (
        wa._handlers[handlers.MessageHandler][0]._callback == instance_with_parentheses
    )


def test_instance_without_parentheses():
    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message  # @wa.on_x
    def instance_without_parentheses(_, __): ...

    assert (
        wa._handlers[handlers.MessageHandler][0]._callback
        == instance_without_parentheses
    )


def test_class_with_parentheses_kw():
    module = ModuleType("module")

    @WhatsApp.on_message(filters=filters.text)  # @WhatsApp.on_x(filters=...) with kw
    def class_with_parentheses_kw(_, __): ...

    module.__dict__["on_message"] = class_with_parentheses_kw
    wa = WhatsApp(server=None, verify_token="1234567890", handlers_modules=[module])
    assert (
        wa._handlers[handlers.MessageHandler][0]._callback == class_with_parentheses_kw
    )


def test_class_with_parentheses_args():
    module = ModuleType("module")

    @WhatsApp.on_message(filters.text)  # @WhatsApp.on_x(filters) without kw
    def class_with_parentheses_args(_, __): ...

    module.__dict__["on_message"] = class_with_parentheses_args
    wa = WhatsApp(server=None, verify_token="1234567890", handlers_modules=[module])
    assert (
        wa._handlers[handlers.MessageHandler][0]._callback
        == class_with_parentheses_args
    )


def test_class_without_parentheses():
    module = ModuleType("module")

    @WhatsApp.on_message
    def class_without_parentheses(_, __): ...

    module.__dict__["on_message"] = class_without_parentheses
    wa = WhatsApp(server=None, verify_token="1234567890", handlers_modules=[module])
    assert (
        wa._handlers[handlers.MessageHandler][0]._callback == class_without_parentheses
    )


def test_all_combinations():
    wa = WhatsApp(server=None, verify_token="1234567890")

    @wa.on_message(filters=filters.text)
    @wa.on_message
    @WhatsApp.on_message(filters=filters.text)
    @WhatsApp.on_message(filters.text)
    @WhatsApp.on_message
    def all_combinations(_, __): ...

    module = ModuleType("module")
    module.__dict__["on_message"] = all_combinations
    wa.load_handlers_modules(module)
    assert len(wa._handlers[handlers.MessageHandler]) == 5


def test_flow_request_decorator():
    @WhatsApp.on_flow_request("/flow")
    def on_flow_class(_, __): ...

    assert isinstance(on_flow_class, handlers.FlowRequestHandler)


def test_add_handlers():
    wa = WhatsApp(server=None, verify_token="xyzxyz")
    h = handlers.MessageHandler(
        callback=lambda _, __: None,
        filters=filters.text,
    )
    wa.add_handlers(h)
    assert wa._handlers[handlers.MessageHandler][0] is h


def test_remove_handlers():
    wa = WhatsApp(server=None, verify_token="xyzxyz")
    h = handlers.MessageHandler(
        callback=lambda _, __: None,
        filters=filters.text,
    )
    wa.add_handlers(h)
    wa.remove_handlers(h)
    assert wa._handlers[handlers.MessageHandler] == []

    with pytest.raises(ValueError):
        wa.remove_handlers(h, silent=False)
    wa.remove_handlers(h, silent=True)


def test_remove_callbacks():
    wa = WhatsApp(server=None, verify_token="xyzxyz")
    c = lambda _, __: None
    mh = handlers.MessageHandler(
        callback=c,
        filters=filters.text,
    )
    ch = handlers.CallbackButtonHandler(
        callback=c,
        filters=filters.text,
    )
    wa.add_handlers(mh, ch)
    wa.remove_callbacks(c)
    assert wa._handlers[handlers.MessageHandler] == []
    assert wa._handlers[handlers.CallbackButtonHandler] == []


def test_get_flow_request_handler():
    wa = WhatsApp(server=None, verify_token="xyzxyz", business_private_key="diuwgcew")
    c = lambda _, __: None
    w = wa.get_flow_request_handler(
        endpoint="/flow",
        callback=c,
    )
    assert w._main_callback is c
