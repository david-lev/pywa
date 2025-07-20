import datetime
import functools
from types import ModuleType

import pytest

from pywa import handlers, types, WhatsApp, filters
from pywa.handlers import FlowRequestHandler, _flow_request_handler_attr
from pywa.types import Message
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
        _client=FAKE_WA,
        wa_id="1234567890",
        name="John",
    ),
    timestamp=datetime.datetime.now(datetime.timezone.utc),
    reply_to_message=types.ReplyToMessage(
        message_id="123",
        from_user_id="1234567890",
        referred_product=None,
    ),
    title="Click me",
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


def test_flow_request_handler():
    @WhatsApp.on_flow_request("/flow")
    def on_flow_class(_, __): ...

    assert isinstance(on_flow_class, handlers.FlowRequestHandler)
    assert hasattr(on_flow_class, _flow_request_handler_attr)

    wa = WhatsApp(server=None, verify_token="1234567890", business_private_key="...")
    on_flow = lambda _, __: ...
    on_flow_instance = wa.get_flow_request_handler(
        endpoint="/flow",
        callback=on_flow,
    )
    assert isinstance(on_flow_instance, handlers.FlowRequestCallbackWrapper)
    assert not hasattr(on_flow_instance, _flow_request_handler_attr)


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
    c = lambda _, __: None
    h = FlowRequestHandler(
        callback=c,
        endpoint="/flow",
    )
    assert h._main_handler is c

    def callback(_, __): ...

    h.add_handler(callback=callback, action=types.FlowRequestActionType.INIT)
    assert h._handlers[(types.FlowRequestActionType.INIT, None)][0][1] is callback


def test_shared_data():
    wa = WhatsApp(server=None, verify_token="xyzxyz")
    msg = Message(
        _client=wa,
        raw={},
        waba_id="456",
        id="123",
        type=types.MessageType.TEXT,
        forwarded=False,
        forwarded_many_times=False,
        reply_to_message=None,
        metadata=types.Metadata(
            display_phone_number="1234567890",
            phone_number_id="1234567890",
        ),
        from_user=types.User(
            _client=wa,
            wa_id="1234567890",
            name="John",
        ),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    @wa.on_message
    def shared_data_handler(_: WhatsApp, m: types.Message):
        m.shared_data["key"] = None
        m.continue_handling()

    @wa.on_message
    def shared_data_check(_: WhatsApp, m: types.Message):
        m.shared_data["key"] = "value"

    wa._invoke_callbacks(
        handler_type=handlers.MessageHandler,
        update=msg,
    )

    assert msg.shared_data["key"] == "value"
