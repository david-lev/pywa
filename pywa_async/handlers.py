"""
Handlers for incoming updates.

>>> from pywa import handlers, filters
>>> from pywa import WhatsApp
>>> wa = WhatsApp(...)

# Register a callback with decorators

>>> @wa.on_message(filters.text)
... async def print_text(wa, m):
...     print(m.text)

>>> wa.remove_callbacks(print_text)

# Register a callback programmatically

>>> print_msg_handler = handlers.MessageHandler(lambda w, m: print(m))
>>> print_txt_handler = handlers.MessageHandler(lambda w, m: print(m.text), filters.text)
>>> wa.add_handlers(print_msg_handler, print_txt_handler)
>>> wa.remove_handlers(print_msg_handler, print_txt_handler)

"""

from __future__ import annotations

__all__ = [
    "MessageHandler",
    "CallbackButtonHandler",
    "CallbackSelectionHandler",
    "RawUpdateHandler",
    "MessageStatusHandler",
    "TemplateStatusHandler",
    "FlowCompletionHandler",
    "FlowRequestHandler",
    "ChatOpenedHandler",
]

import abc

from pywa.handlers import (
    _resolve_factory,
    _get_factored_update,
)
import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, TypeAlias, Awaitable, cast

from . import utils
from .types import (
    CallbackButton,
    CallbackSelection,
    Message,
    MessageStatus,
    TemplateStatus,
    FlowRequest,
    FlowResponse,
    ChatOpened,
    CallbackData,
)
from .types.flows import FlowCompletion, FlowResponseError  # noqa

if TYPE_CHECKING:
    from .client import WhatsApp
    from .types.base_update import BaseUpdate  # noqa

_CallbackDataFactoryT: TypeAlias = (
    type[str]
    | type[CallbackData]
    | tuple[type[CallbackData | Any], ...]
    | list[type[CallbackData | Any]]
    | Callable[[str], Any | Awaitable[Any]]
)
"""Type hint for the callback data factory."""

_FlowRequestHandlerT: TypeAlias = Callable[
    ["WhatsApp", FlowRequest],
    FlowResponse
    | FlowResponseError
    | dict
    | None
    | Awaitable[FlowResponse | FlowResponseError | dict | None],
]
"""Type hint for the flow request handler."""


class Handler(abc.ABC):
    """Base class for all handlers."""

    @property
    @abc.abstractmethod
    def _field_name(self) -> str | None:
        """
        The field name of the webhook update
        https://developers.facebook.com/docs/graph-api/webhooks/reference/whatsapp-business-account
        """

    @property
    @abc.abstractmethod
    def _update_constructor(self) -> Callable[[WhatsApp, dict], BaseUpdate]:
        """The constructor to use to construct the update object from the webhook update dict."""

    def __init__(
        self,
        callback: Callable[[WhatsApp, Any], Any],
        *filters: Callable[[WhatsApp, Any], bool],
    ):
        """
        Initialize a new callback.
        """
        self.callback = callback
        self.filters = filters

    async def handle(self, wa: WhatsApp, data: Any):
        for f in self.filters:
            if inspect.iscoroutinefunction(f):
                if not await f(wa, data):
                    return
            elif not f(wa, data):
                return

        if inspect.iscoroutinefunction(self.callback):
            await self.callback(wa, data)
        else:
            await wa._loop.run_in_executor(
                wa._executor,
                self.callback,
                wa,
                data,
            )

    @staticmethod
    @functools.cache
    def _fields_to_subclasses() -> dict[str, Handler]:
        """
        Return a dict of all the subclasses of `Handler` with their field name as the key.
        (e.g. ``{'messages': MessageHandler}``)

        **IMPORTANT:** This function is for internal use only, DO NOT USE IT to get the available handlers
        (use ``Handler.__subclasses__()`` instead).

        **IMPORTANT:** This function is cached, so if you subclass `Handler` after calling this function, the new class
        will not be included in the returned dict.
        """
        return cast(
            dict[str, Handler],
            {
                h._field_name: h
                for h in Handler.__subclasses__()
                if h._field_name is not None
            },
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(callback={self.callback!r}, filters={self.filters!r})"

    def __repr__(self) -> str:
        return self.__str__()


class MessageHandler(Handler):
    """
    Handler for incoming :class:`pywa.types.Message`.

    - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a callback for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_text_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageHandler(print_text_messages, fil.text))

    Args:
        callback: The callback function (Takes the :class:`pywa.WhatsApp` instance and a :class:`pywa.types.Message` as
         arguments)
        *filters: The filters to apply to the callback (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.Message` and returns a :class:`bool`)
    """

    _field_name = "messages"
    _update_constructor = Message.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, Message], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, Message], bool | Awaitable[bool]],
    ):
        super().__init__(callback, *filters)


class CallbackButtonHandler(Handler):
    """
    Handler for callback buttons (User clicks on a :class:`pywa.types.Button`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_btn = lambda _, btn: print(btn)
        >>> wa.add_handlers(CallbackButtonHandler(print_btn, fil.startswith('id:')))

    Args:
        callback: The callback function (gets the WhatsApp instance and the callback as arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackButton` and returns a :class:`bool`)
        factory: The constructor/s to use to construct the callback data (default: :class:`str`. If the factory is a
         subclass of :class:`CallbackData`, a matching filter is automatically added).
        factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
         filters will get the callback data after the factory is applied).
    """

    _field_name = "messages"
    _update_constructor = CallbackButton.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, CallbackButton], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
    ):
        (
            self.factory,
            self.factory_filter,
        ) = _resolve_factory(factory, "data")
        self.factory_before_filters = factory_before_filters
        super().__init__(callback, *filters)

    async def handle(self, wa: WhatsApp, clb: CallbackButton):
        update = await _get_factored_update(self, wa, clb, "data")
        if update is not None:
            if inspect.iscoroutinefunction(self.callback):
                await self.callback(wa, update)
            else:
                await wa._loop.run_in_executor(
                    wa._executor,
                    self.callback,
                    wa,
                    update,
                )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(callback={self.callback!r}, filters={self.filters!r}, factory={self.factory!r})"


class CallbackSelectionHandler(Handler):
    """
    Handler for callback selections (User selects an option from :class:`pywa.types.SectionList`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_selection = lambda _, sel: print(sel)
        >>> wa.add_handlers(CallbackSelectionHandler(print_selection, fil.startswith('id:')))

    Args:
        callback: The callback function. (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackSelection` as arguments)
        *filters: The filters to apply to the handler. (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackSelection` and returns a :class:`bool`)
        factory: The constructor/s to use to construct the callback data (default: :class:`str`. If the factory is a
         subclass of :class:`CallbackData`, a matching filter is automatically added).
        factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
         filters will get the callback data after the factory is applied).
    """

    _field_name = "messages"
    _update_constructor = CallbackSelection.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, CallbackSelection], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
    ):
        (
            self.factory,
            self.factory_filter,
        ) = _resolve_factory(factory, "data")
        self.factory_before_filters = factory_before_filters
        super().__init__(callback, *filters)

    async def handle(self, wa: WhatsApp, sel: CallbackSelection):
        update = await _get_factored_update(self, wa, sel, "data")
        if update is not None:
            if inspect.iscoroutinefunction(self.callback):
                await self.callback(wa, update)
            else:
                await wa._loop.run_in_executor(
                    wa._executor,
                    self.callback,
                    wa,
                    update,
                )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(callback={self.callback!r}, filters={self.filters!r}, factory={self.factory!r})"


class MessageStatusHandler(Handler):
    """
    Handler for :class:`pywa.types.MessageStatus` updates (Message is sent, delivered, read, failed, etc...).

    - You can use the :func:`~pywa.client.WhatsApp.on_message_status` decorator to register a handler for this type.

    **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_failed_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageStatusHandler(print_failed_messages, fil.message_status.failed))

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a :class:`pywa.types.MessageStatus` as
            arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.MessageStatus` and returns a :class:`bool`)
        factory: The constructor/s to use to construct the tracker data (default: :class:`str`. If the factory is a
            subclass of :class:`CallbackData`, a matching filter is automatically added).
        factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
            filters will get the tracker data after the factory is applied).
    """

    _field_name = "messages"
    _update_constructor = MessageStatus.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, MessageStatus], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
    ):
        (
            self.factory,
            self.factory_filter,
        ) = _resolve_factory(factory, "tracker")
        self.factory_before_filters = factory_before_filters
        super().__init__(callback, *filters)

    async def handle(self, wa: WhatsApp, status: MessageStatus):
        update = await _get_factored_update(self, wa, status, "tracker")
        if update is not None:
            if inspect.iscoroutinefunction(self.callback):
                await self.callback(wa, update)
            else:
                await wa._loop.run_in_executor(
                    wa._executor,
                    self.callback,
                    wa,
                    update,
                )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(callback={self.callback!r}, filters={self.filters!r}, factory={self.factory!r})"


class ChatOpenedHandler(Handler):
    """
    Handler for :class:`pywa.types.ChatOpened`

    - You can use the :func:`~pywa.client.WhatsApp.on_chat_opened` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_chat_opened = lambda _, msg: print(msg)
        >>> wa.add_handlers(ChatOpenedHandler(print_chat_opened))

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.ChatOpened` as arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.ChatOpened` and returns a :class:`bool`)

    """

    _field_name = "messages"
    _update_constructor = ChatOpened.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, ChatOpened], bool | Awaitable[bool]],
    ):
        super().__init__(callback, *filters)


class TemplateStatusHandler(Handler):
    """
    Handler for :class:`pywa.types.TemplateStatus` updates (Template message is approved, rejected etc...).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_status` decorator to register a handler for this type.


    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_template_status = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateStatusHandler(
        ...     print_template_status,
        ...     fil.template_status.on_event(TemplateStatus.TemplateEvent.APPROVED)
        ... ))

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.TemplateStatus` as arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.TemplateStatus` and returns a :class:`bool`)
    """

    _field_name = "message_template_status_update"
    _update_constructor = TemplateStatus.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, TemplateStatus], bool | Awaitable[bool]],
    ):
        super().__init__(callback, *filters)


class FlowCompletionHandler(Handler):
    """
    Handler for :class:`pywa.types.FlowCompletion` updates (Flow is completed).

    - You can use the :func:`~pywa.client.WhatsApp.on_flow_completion` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_flow = lambda _, flow: print(flow)
        >>> wa.add_handlers(FlowCompletionHandler(print_flow)

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.FlowCompletion` as arguments)

    """

    _field_name = "messages"
    _update_constructor = FlowCompletion.from_update

    def __init__(
        self,
        callback: Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, FlowCompletion], bool | Awaitable[bool]],
    ):
        super().__init__(callback, *filters)


class RawUpdateHandler(Handler):
    """
    A raw update callback.

    - This handler will be called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
    - You can use the :func:`~pywa.client.WhatsApp.on_raw_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_updates = lambda _, data: print(data)
        >>> wa.add_handlers(RawUpdateHandler(print_updates))

    Args:
        handler: The callback function (Takes a :class:`pywa.WhatsApp` instance and a :class:`dict` as arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a :class:`dict` and
            returns a :class:`bool`)
    """

    _field_name = None
    _update_constructor = lambda _, data: data  # noqa

    def __init__(
        self,
        callback: Callable[[WhatsApp, dict], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, dict], bool | Awaitable[bool]],
    ):
        super().__init__(callback, *filters)


class FlowRequestHandler:
    """
    A handler for Flow Data Exchange requests.

    Args:
        callback: The function to call when a request is received (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.FlowRequest` as arguments and returns a :class:`pywa.types.FlowResponse`.
        endpoint: The endpoint to listen to (The endpoint uri you set to the flow. e.g ``/feedback_flow``).
        acknowledge_errors: Whether to acknowledge errors (The return value of the callback will be ignored, and
         pywa will acknowledge the error automatically).
        handle_health_check: Whether to handle health checks (The callback will not be called for health checks).
        private_key: The private key to use to decrypt the requests (Override the global ``business_private_key``).
        private_key_password: The password to use to decrypt the private key (Override the global ``business_private_key_password``).
        request_decryptor: The function to use to decrypt the requests (Override the global ``flows_request_decryptor``)
        response_encryptor: The function to use to encrypt the responses (Override the global ``flows_response_encryptor``)
    """

    def __init__(
        self,
        callback: _FlowRequestHandlerT,
        *,
        endpoint: str,
        acknowledge_errors: bool = True,
        handle_health_check: bool = True,
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ):
        self.callback = callback
        self.endpoint = endpoint
        self.acknowledge_errors = acknowledge_errors
        self.handle_health_check = handle_health_check
        self.private_key = private_key
        self.private_key_password = private_key_password
        self.request_decryptor = request_decryptor
        self.response_encryptor = response_encryptor
