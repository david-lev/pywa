"""
Handlers for incoming updates.

>>> from pywa import handlers, filters
>>> from pywa import WhatsApp
>>> wa = WhatsApp(...)

# Register a callback with decorators

>>> @wa.on_message(filters.text)
... def print_text(wa, m):
...     print(m.text)

# Or when you don't have access yet to the WhatsApp instance

# my_handlers.py
>>> @WhatsApp.on_callback_button(filters.text)
... def print_text(wa, m):
...     print(m.text)
# main.py
>>> from . import my_handlers
>>> wa = WhatsApp(handlers_modules=[my_handlers])
# Or
>>> wa.load_handlers_modules(my_handlers)

# Remove a callback
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
import collections
import dataclasses
import functools
import logging
from typing import TYPE_CHECKING, Any, Callable, cast, TypeAlias, Awaitable, TypedDict

from . import utils
from .filters import Filter
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
from .types.flows import (
    FlowCompletion,
    FlowResponseError,
    FlowRequestActionType,
    FlowRequestCannotBeDecrypted,
    Screen,
)  # noqa

if TYPE_CHECKING:
    from .client import WhatsApp
    from .types.base_update import BaseUpdate  # noqa

_FlowRequestHandlerT: TypeAlias = Callable[
    ["WhatsApp", FlowRequest],
    FlowResponse
    | FlowResponseError
    | dict
    | None
    | Awaitable[FlowResponse | FlowResponseError | dict | None],
]
"""Type hint for the flow request handler."""

_RawUpdateCallback: TypeAlias = Callable[["WhatsApp", dict], Any | Awaitable[Any]]
_MessageCallback: TypeAlias = Callable[["WhatsApp", Message], Any | Awaitable[Any]]
_CallbackButtonCallback: TypeAlias = Callable[
    ["WhatsApp", CallbackButton], Any | Awaitable[Any]
]
_CallbackSelectionCallback: TypeAlias = Callable[
    ["WhatsApp", CallbackSelection], Any | Awaitable[Any]
]
_MessageStatusCallback: TypeAlias = Callable[
    ["WhatsApp", MessageStatus], Any | Awaitable[Any]
]
_ChatOpenedCallback: TypeAlias = Callable[
    ["WhatsApp", ChatOpened], Any | Awaitable[Any]
]
_TemplateStatusCallback: TypeAlias = Callable[
    ["WhatsApp", TemplateStatus], Any | Awaitable[Any]
]
_FlowCompletionCallback: TypeAlias = Callable[
    ["WhatsApp", FlowCompletion], Any | Awaitable[Any]
]


class EncryptedFlowRequestType(TypedDict):
    """Encrypted Flow Request Type."""

    encrypted_flow_data: str
    encrypted_aes_key: str
    initial_vector: str


_logger = logging.getLogger(__name__)

_FactorySupported: TypeAlias = CallbackButton | CallbackSelection | MessageStatus


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
    def _is_user_update(self) -> bool:
        """
        Whether the update is a user update or not.
        """

    def __init__(
        self,
        callback: Callable[[WhatsApp, Any | dict], Any | Awaitable[Any]],
        filters: Filter | None,
        priority: int,
    ):
        """
        Initialize a new callback.
        """
        self._callback = callback
        self._filters = filters
        self._priority = priority
        self._is_async_callback = utils.is_async_callable(callback)

    def check(self, wa: WhatsApp, update: BaseUpdate | dict) -> bool:
        return self._filters is None or self._filters.check_sync(wa, update)

    def handle(self, wa: WhatsApp, update: BaseUpdate | dict) -> bool:
        if not self.check(wa, update):
            return False
        self._callback(wa, update)
        return True

    async def acheck(self, wa: WhatsApp, update: BaseUpdate | dict) -> bool:
        return self._filters is None or await self._filters.check_async(wa, update)

    async def ahandle(self, wa: WhatsApp, update: BaseUpdate | dict) -> bool:
        if not await self.acheck(wa, update):
            return False
        await self._callback(wa, update) if self._is_async_callback else self._callback(
            wa, update
        )
        return True

    @staticmethod
    @functools.cache
    def _fields_to_subclasses() -> dict[str, type[Handler]]:
        """
        Return a dict of all the subclasses of `Handler` with their field name as the key.
        (e.g. ``{'messages': MessageHandler}``)

        **IMPORTANT:** This function is for internal use only, DO NOT USE IT to get the available handlers
        (use ``Handler.__subclasses__()`` instead).

        **IMPORTANT:** This function is cached, so if you subclass `Handler` after calling this function, the new class
        will not be included in the returned dict.
        """
        return cast(
            dict[str, type[Handler]],
            {
                h._field_name: h
                for h in Handler.__subclasses__()
                if h._field_name is not None
            },
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(callback={self._callback}, filters={self._filters}, priority={self._priority})"

    def __str__(self) -> str:
        return self.__repr__()


class MessageHandler(Handler):
    """
    Handler for incoming :class:`pywa.types.Message`.

    - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a callback for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_text_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageHandler(print_text_messages, filters.text))

    Args:
        callback: The callback function (Takes the :class:`pywa.WhatsApp` instance and a :class:`pywa.types.Message` as
         arguments)
        filters: The filters to apply to the callback
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = "messages"
    _is_user_update = True

    def __init__(
        self,
        callback: _MessageCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class _FactoryHandler(Handler):
    """Base class for handlers that use a factory to construct the callback data."""

    _field_name = "messages"
    _data_field: str
    _is_user_update = True

    def __init__(
        self,
        callback: Callable[[WhatsApp, _FactorySupported], Any | Awaitable[Any]],
        filters: Filter | None,
        factory: type[CallbackData] | None,
        priority: int,
    ):
        self._factory = factory
        super().__init__(callback=callback, filters=filters, priority=priority)

    def _process_update(self, update: _FactorySupported) -> _FactorySupported | None:
        if self._factory:
            raw_data = getattr(update, self._data_field)
            if raw_data is None or not raw_data.startswith(
                f"{self._factory.__callback_id__}{self._factory.__callback_data_sep__}"
            ):
                return None
            if (data := getattr(update, self._data_field)) is None:
                return None
            update = dataclasses.replace(
                update, **{self._data_field: self._factory.from_str(data)}
            )
        return update

    def handle(self, wa: WhatsApp, update: _FactorySupported) -> bool:
        update = self._process_update(update)
        if update is None:
            return False
        return super().handle(wa, update)

    async def ahandle(self, wa: WhatsApp, update: _FactorySupported) -> bool:
        update = self._process_update(update)
        if update is None:
            return False
        return await super().ahandle(wa, update)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(callback={self._callback}, filters={self._filters}, factory={self._factory}, priority={self._priority})"


class CallbackButtonHandler(_FactoryHandler):
    """
    Handler for callback buttons (User clicks on a :class:`pywa.types.Button`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_btn = lambda _, btn: print(btn)
        >>> wa.add_handlers(CallbackButtonHandler(print_btn, filters.startswith('id:')))

    Args:
        callback: The callback function (gets the WhatsApp instance and the callback as arguments)
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackButton` and returns a :class:`bool`)
        factory: The constructor to use to construct the callback data.
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "data"

    def __init__(
        self,
        callback: _CallbackButtonCallback,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ):
        super().__init__(
            callback=callback,
            filters=filters,
            factory=factory,
            priority=priority,
        )


class CallbackSelectionHandler(_FactoryHandler):
    """
    Handler for callback selections (User selects an option from :class:`pywa.types.SectionList`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_selection = lambda _, sel: print(sel)
        >>> wa.add_handlers(CallbackSelectionHandler(print_selection, filters.startswith('id:')))

    Args:
        callback: The callback function. (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackSelection` as arguments)
        filters: The filters to apply to the handler
        factory: The constructor to use to construct the callback data.
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "data"

    def __init__(
        self,
        callback: _CallbackSelectionCallback,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ):
        super().__init__(
            callback=callback,
            filters=filters,
            factory=factory,
            priority=priority,
        )


class MessageStatusHandler(_FactoryHandler):
    """
    Handler for :class:`pywa.types.MessageStatus` updates (Message is sent, delivered, read, failed, etc...).

    - You can use the :func:`~pywa.client.WhatsApp.on_message_status` decorator to register a handler for this type.

    **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

    Example:

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)
        >>> print_failed_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageStatusHandler(print_failed_messages, filters.failed))

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a :class:`pywa.types.MessageStatus` as
            arguments)
        filters: The filters to apply to the handler
        factory: The constructor to use to construct the callback data.
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "tracker"

    def __init__(
        self,
        callback: _MessageStatusCallback,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ):
        super().__init__(
            callback=callback,
            filters=filters,
            factory=factory,
            priority=priority,
        )


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
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)

    """

    _field_name = "messages"
    _is_user_update = True

    def __init__(
        self,
        callback: _ChatOpenedCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class TemplateStatusHandler(Handler):
    """
    Handler for :class:`pywa.types.TemplateStatus` updates (Template message is approved, rejected etc...).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_status` decorator to register a handler for this type.


    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_template_status = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateStatusHandler(print_template_status))

    Args:
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.TemplateStatus` as arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = "message_template_status_update"
    _is_user_update = False

    def __init__(
        self,
        callback: _TemplateStatusCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


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
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)

    """

    _field_name = "messages"
    _is_user_update = True

    def __init__(
        self,
        callback: _FlowCompletionCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


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
        callback: The callback function (Takes a :class:`pywa.WhatsApp` instance and a :class:`dict` as arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = None
    _is_user_update = False

    def __init__(
        self,
        callback: _RawUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


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
        self._callback = callback
        self._on_callbacks: dict[
            tuple[FlowRequestActionType | str, str | None],
            list[tuple[Filter | None, _FlowRequestHandlerT]],
        ] = collections.defaultdict(list)  # {(action, screen?): [(filters?, callback)]}
        self._error_callback = None
        self._endpoint = endpoint
        self._acknowledge_errors = acknowledge_errors
        self._handle_health_check = handle_health_check
        self._private_key = private_key
        self._private_key_password = private_key_password
        self._request_decryptor = request_decryptor
        self._response_encryptor = response_encryptor

    def on(
        self,
        *,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to help you add more handlers to the same endpoint and split the logic into multiple functions.

        Example:

            >>> @WhatsApp.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    if req.has_error: print(req.data)
            >>> @feedback_flow_handler.on(action=FlowRequestActionType.INIT)
            >>> def on_init(_: WhatsApp, req: FlowRequest):
            ...     ...
            >>> @feedback_flow_handler.on(action=FlowRequestActionType.DATA_EXCHANGE, screen="SURVEY")
            >>> def on_survey_data_exchange(_: WhatsApp, req: FlowRequest):
            ...     ...
            >>> @feedback_flow_handler.on(..., data_filter=filters.new(lambda _, data: data.get("rating") == 5))
            >>> def on_rating_5(_: WhatsApp, req: FlowRequest):
            ...     ...

        Args:
            action: The action type to listen to.
            screen: The screen ID to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The function itself.
        """

        def decorator(callback: _FlowRequestHandlerT):
            self._on_callbacks[(action, screen)].append((filters, callback))
            return callback

        return decorator

    def on_errors(
        self=None, clb=_FlowRequestHandlerT
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add an error handler to the current endpoint.

        - Shortcut for :func:`~pywa.client.FlowRequestCallbackWrapper.set_errors_handler`.

        Example:

            >>> @WhatsApp.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...
            >>> @feedback_flow_handler.on_errors
            >>> def on_error(_: WhatsApp, req: FlowRequest):
            ...     logging.error("An error occurred: %s", req.data)

        Returns:
            The function itself.
        """
        if clb:  # @main_callback.on_errors
            self._error_callback = clb
            return clb

        def decorator(callback: _FlowRequestHandlerT):  # @main_callback.on_errors()
            self._error_callback = callback
            return callback

        return decorator


_flow_request_handler_attr = "__pywa_flow_request_handler"
setattr(FlowRequestHandler, _flow_request_handler_attr, None)


class HandlerDecorators:
    """This class is used by the :class:`WhatsApp` client to register handlers using decorators."""

    def __init__(self: WhatsApp):
        raise TypeError("This class cannot be instantiated.")

    def on_raw_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> Callable[[_RawUpdateCallback], _RawUpdateCallback] | _RawUpdateCallback:
        """
        Decorator to register a function as a callback for raw updates (:class:`dict`).

        - This callback is called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`RawUpdateHandler`.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_raw_update
            ... def raw_update_handler(_: WhatsApp, update: dict):
            ...     print(update)

        Args:
            filters: Filters to apply to the incoming updates.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=RawUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _RawUpdateCallback) -> _RawUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=RawUpdateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_message(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> Callable[[_MessageCallback], _MessageCallback] | _MessageCallback:
        """
        Decorator to register a function as a callback for incoming :class:`pywa.types.Message` (User sends a message).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`MessageHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_message(filters.matches("Hello", "Hi", ignore_case=True))
            ... def hello_handler(_: WhatsApp, msg: types.Message):
            ...     msg.react("👋")
            ...     msg.reply_text(text="Hello from PyWa!", quote=True)

        Args:
            filters: Filters to apply to the incoming messages.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=MessageHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _MessageCallback) -> _MessageCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=MessageHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_callback_button(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ) -> (
        Callable[[_CallbackButtonCallback], _CallbackButtonCallback]
        | _CallbackButtonCallback
    ):
        """
        Decorator to register a function as a callback when a user clicks on a :class:`pywa.types.Button`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackButtonHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_button(filters.matches("help"))
            ... def help_handler(_: WhatsApp, btn: types.CallbackButton):
            ...     btn.reply_text(text="What can I help you with?")

        Args:
            filters: Filters to apply to the incoming callback button presses.
            factory: The constructor to use to construct the callback data.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallbackButtonHandler,
                filters=filters,
                priority=priority,
                factory=factory,
            )
        ) is not None:
            return clb

        def deco(callback: _CallbackButtonCallback) -> _CallbackButtonCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallbackButtonHandler,
                callback=callback,
                filters=filters,
                priority=priority,
                factory=factory,
            )

        return deco

    def on_callback_selection(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ) -> (
        Callable[[_CallbackSelectionCallback], _CallbackSelectionCallback]
        | _CallbackSelectionCallback
    ):
        """
        Decorator to register a function as a callback when a user selects an option from a :class:`pywa.types.SectionList`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackSelectionHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_selection(filters.startswith("id:"))
            ... def id_handler(_: WhatsApp, sel: types.CallbackSelection):
            ...     sel.reply_text(text=f"Your ID is {sel.data.split(':', 1)[1]}")

        Args:
            filters: Filters to apply to the incoming callback selections.
            factory: The constructor to use to construct the callback data.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallbackSelectionHandler,
                filters=filters,
                priority=priority,
                factory=factory,
            )
        ) is not None:
            return clb

        def deco(callback: _CallbackSelectionCallback) -> _CallbackSelectionCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallbackSelectionHandler,
                callback=callback,
                filters=filters,
                priority=priority,
                factory=factory,
            )

        return deco

    def on_message_status(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ) -> (
        Callable[[_MessageStatusCallback], _MessageStatusCallback]
        | _MessageStatusCallback
    ):
        """
        Decorator to register a function as a callback for incoming message status changes (Message is sent, delivered,
        read, failed, etc...).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`MessageStatusHandler`.

        **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_message_status(filters.failed)
            ... def delivered_handler(client: WhatsApp, status: types.MessageStatus):
            ...     print(f"Message {status.id} failed to send to {status.from_user.wa_id}: {status.error.message})


        Args:
            filters: Filters to apply to the incoming message status changes.
            factory: The constructor to use to construct the callback data.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=MessageStatusHandler,
                filters=filters,
                priority=priority,
                factory=factory,
            )
        ) is not None:
            return clb

        def deco(callback: _MessageStatusCallback) -> _MessageStatusCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=MessageStatusHandler,
                callback=callback,
                filters=filters,
                priority=priority,
                factory=factory,
            )

        return deco

    def on_chat_opened(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> Callable[[_ChatOpenedCallback], _ChatOpenedCallback] | _ChatOpenedCallback:
        """
        Decorator to register a function as a callback for incoming chat opened (User opens a chat).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`ChatOpenedHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_chat_opened
            ... def chat_opened_handler(client: WhatsApp, chat_opened: types.ChatOpened):
            ...     print(f"The user {chat_opened.from_user.wa_id} just opened a chat with us!")

        Args:
            filters: Filters to apply to the incoming chat opened.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=ChatOpenedHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _ChatOpenedCallback) -> _ChatOpenedCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=ChatOpenedHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_template_status(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_TemplateStatusCallback], _TemplateStatusCallback]
        | _TemplateStatusCallback
    ):
        """
        Decorator to register a function as a callback for :class:`pywa.types.TemplateStatus` updates (Template message
        is approved, rejected etc...).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`TemplateStatusHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_status
            ... def approved_handler(client: WhatsApp, status: types.TemplateStatus):
            ...     print(f"Template {status.message_template_name} just got {status.event}!")

        Args:
            filters: Filters to apply to the incoming template status changes.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=TemplateStatusHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _TemplateStatusCallback) -> _TemplateStatusCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=TemplateStatusHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_flow_completion(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_FlowCompletionCallback], _FlowCompletionCallback]
        | _FlowCompletionCallback
    ):
        """
        Decorator to register a function as a callback for :class:`pywa.types.FlowCompletion` updates (Flow is completed).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`FlowCompletionHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_completion
            ... def flow_handler(client: WhatsApp, flow: types.FlowCompletion):
            ...     print(f"Flow {flow.token} just got completed!. Flow data: {flow.response}")

        Args:
            filters: Filters to apply to the incoming flow completion.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=FlowCompletionHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _FlowCompletionCallback) -> _FlowCompletionCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=FlowCompletionHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_flow_request(
        self: WhatsApp | str = None,
        endpoint: str = None,
        *,
        acknowledge_errors: bool = True,
        handle_health_check: bool = True,
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ) -> Callable[
        [_FlowRequestHandlerT],
        FlowRequestCallbackWrapper | FlowRequestHandler,
    ]:
        """
        Decorator to register a function to handle and respond to incoming flow requests.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(business_private_key='...', ...)
            >>> @wa.on_flow_request('/feedback_flow')
            ... def feedback_flow_handler(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     ...

            >>> @feedback_flow_handler.on(types.FlowRequestActionType.DATA_EXCHANGE, screen="SURVEY")
            ... def survey_data_handler(_: WhatsApp, req: FlowRequest):
            ...     ...

        Args:
            endpoint: The endpoint to listen to (The endpoint uri you set to the flow. e.g ``/feedback_flow``).
            acknowledge_errors: Whether to acknowledge errors (The return value of the callback will be ignored, and
             pywa will acknowledge the error automatically).
            handle_health_check: Whether to handle health checks (The callback will not be called for health checks).
            private_key: The private key to use to decrypt the requests (Override the global ``business_private_key``).
            private_key_password: The password to use to decrypt the private key (Override the global ``business_private_key_password``).
            request_decryptor: The function to use to decrypt the requests (Override the global ``flows_request_decryptor``)
            response_encryptor: The function to use to encrypt the responses (Override the global ``flows_response_encryptor``)
        """

        def decorator(
            callback: _FlowRequestHandlerT,
        ) -> FlowRequestCallbackWrapper | FlowRequestHandler:
            if self is None or isinstance(self, str):
                ep = self or endpoint
                if not ep:
                    raise ValueError("The endpoint must be provided.")
                return FlowRequestHandler(
                    callback=callback,
                    endpoint=ep,
                    acknowledge_errors=acknowledge_errors,
                    handle_health_check=handle_health_check,
                    private_key=private_key,
                    private_key_password=private_key_password,
                    request_decryptor=request_decryptor,
                    response_encryptor=response_encryptor,
                )

            callback_wrapper = self._register_flow_endpoint_callback(
                endpoint=endpoint,
                callback=callback,
                acknowledge_errors=acknowledge_errors,
                handle_health_check=handle_health_check,
                private_key=private_key,
                private_key_password=private_key_password,
                request_decryptor=request_decryptor,
                response_encryptor=response_encryptor,
            )
            return callback_wrapper

        return decorator


_handlers_attr = "__pywa_handlers"


def _registered_without_parentheses(
    *,
    self: WhatsApp,
    handler_type: type[Handler],
    filters: Filter,
    priority: int,
    **kwargs,
) -> Callable | None:
    """When the decorator is called without parentheses."""
    if callable(self) and filters is None:  # @WhatsApp.on_x
        _register_func_handler(
            handler_type=handler_type,
            callback=self,
            filters=None,
            priority=priority,
            **kwargs,
        )
        return self
    elif callable(filters):  # @wa.on_x
        self.add_handlers(
            handler_type(callback=filters, filters=None, priority=priority, **kwargs)
        )
        return filters
    return None


def _registered_with_parentheses(
    *,
    self: WhatsApp,
    handler_type: type[Handler],
    callback: Callable,
    filters: Filter,
    priority: int,
    **kwargs,
) -> Callable:
    """When the decorator is called with parentheses."""
    if self is None or isinstance(
        self, Filter
    ):  # @WhatsApp.on_x(filters=...) | @WhatsApp.on_x(filters.text)
        _register_func_handler(
            handler_type=handler_type,
            callback=callback,
            filters=self or filters,
            priority=priority,
            **kwargs,
        )
    else:  # @wa.on_x(filters.text)
        self.add_handlers(
            handler_type(
                callback=callback, filters=filters, priority=priority, **kwargs
            )
        )
    return callback


def _register_func_handler(
    handler_type: type[Handler],
    callback: Callable,
    filters: Filter | None,
    priority: int,
    **kwargs,
):
    if not hasattr(callback, _handlers_attr):
        setattr(callback, _handlers_attr, [])
    getattr(callback, _handlers_attr).append(
        handler_type(callback=callback, filters=filters, priority=priority, **kwargs)
    )


class FlowRequestCallbackWrapper:
    """
    This is a wrapper class for the flow request callback.
    It allows you to add more handlers to the same endpoint and split the logic into multiple functions.

    - THIS CLASS IS NOT MEANT TO BE INSTANTIATED DIRECTLY!
    """

    def __init__(
        self,
        wa: WhatsApp,
        endpoint: str,
        callback: _FlowRequestHandlerT,
        acknowledge_errors: bool = True,
        handle_health_check: bool = True,
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ):
        self._wa = wa
        self._endpoint = endpoint
        wa._check_for_async_callback(callback)
        self._main_callback = callback
        self._error_callback: _FlowRequestHandlerT | None = None
        self._on_callbacks: dict[
            tuple[FlowRequestActionType | str, str | None],
            list[tuple[Filter | None, _FlowRequestHandlerT]],
        ] = collections.defaultdict(list)  # {(action, screen?): [(filters?, callback)]}
        self._acknowledge_errors = acknowledge_errors
        self._handle_health_check = handle_health_check
        self._private_key = private_key or wa._private_key
        self._private_key_password = private_key_password or wa._private_key_password

        if self._endpoint == wa._webhook_endpoint:
            raise ValueError(
                "The flow endpoint cannot be the same as the WhatsApp webhook endpoint."
            )
        if not self._private_key:
            raise ValueError(
                "A private_key must be provided in order to decrypt incoming requests. You can provide it when "
                "initializing the WhatsApp client or when registering the flow request callback."
            )
        self._request_decryptor = request_decryptor or wa._flows_request_decryptor
        if not self._request_decryptor:
            raise ValueError(
                "A `request_decryptor` must be provided in order to decrypt incoming requests. You can provide it when "
                "initializing the WhatsApp client or when registering the flow request callback."
            )
        self._response_encryptor = response_encryptor or wa._flows_response_encryptor
        if not self._response_encryptor:
            raise ValueError(
                "A `response_encryptor` must be provided in order to encrypt outgoing responses. You can provide it "
                "when initializing the WhatsApp client or when registering the flow request callback."
            )
        if (
            self._request_decryptor is utils.default_flow_request_decryptor
            or self._response_encryptor is utils.default_flow_response_encryptor
        ) and not utils.is_installed("cryptography"):
            raise ValueError(
                "The default decryptor/encryptor requires the `cryptography` package to be installed."
                '\n>> Install it with `pip install cryptography` / pip install "pywa[cryptography]" or use a '
                "custom decryptor/encryptor."
            )

    def on(
        self,
        *,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to help you add more handlers to the same endpoint and split the logic into multiple functions.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    if req.has_error: print(req.data)
            >>> @feedback_flow_handler.on(action=FlowRequestActionType.INIT)
            >>> def on_init(_: WhatsApp, req: FlowRequest):
            ...     ...
            >>> @feedback_flow_handler.on(action=FlowRequestActionType.DATA_EXCHANGE, screen="SURVEY")
            >>> def on_survey_data_exchange(_: WhatsApp, req: FlowRequest):
            ...     ...
            >>> @feedback_flow_handler.on(..., data_filter=filters.new(lambda _, data: data.get("rating") == 5))
            >>> def on_rating_5(_: WhatsApp, req: FlowRequest):
            ...     ...

        Args:
            action: The action type to listen to.
            screen: The screen ID to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The function itself.
        """

        def decorator(callback: _FlowRequestHandlerT):
            self.add_handler(
                callback=callback, action=action, screen=screen, filters=filters
            )
            return callback

        return decorator

    def on_errors(
        self=None, clb=_FlowRequestHandlerT
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add an error handler to the current endpoint.

        - Shortcut for :func:`~pywa.client.FlowRequestCallbackWrapper.set_errors_handler`.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...
            >>> @feedback_flow_handler.on_errors
            >>> def on_error(_: WhatsApp, req: FlowRequest):
            ...     logging.error("An error occurred: %s", req.data)

        Returns:
            The function itself.
        """
        if clb:  # @main_callback.on_errors
            self.set_errors_handler(callback=clb)
            return clb

        def decorator(callback: _FlowRequestHandlerT):  # @main_callback.on_errors()
            self.set_errors_handler(callback)
            return callback

        return decorator

    def add_handler(
        self,
        *,
        callback: _FlowRequestHandlerT,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> FlowRequestCallbackWrapper:
        """
        Add a handler to the current endpoint.

        - You can add multiple handlers to the same endpoint and split the logic into multiple functions.

        Example:

            >>> wa = WhatsApp(...)
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...
            >>> on_init = lambda _, req: ...
            >>> on_survey_data_exchange = lambda _, req: ...
            >>> wa.add_flow_request_handler(
            ...     FlowRequestHandler(callback=feedback_flow_handler, endpoint="/feedback_flow")
            ... ).add_handler(callback=on_init, action=FlowRequestActionType.INIT)
            ...  .add_handler(callback=on_survey_data_exchange, action=FlowRequestActionType.DATA_EXCHANGE, screen="SURVEY")


        Args:
            callback: The callback function to handle this particular request.
            action: The action type to listen to.
            screen: The screen ID to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The current instance.
        """
        self._wa._check_for_async_callback(callback)
        self._wa._check_for_async_filters(filters)
        self._on_callbacks[
            (action, screen.id if isinstance(screen, Screen) else screen)
        ].append((filters, callback))
        return self

    def set_errors_handler(
        self, callback: _FlowRequestHandlerT
    ) -> FlowRequestCallbackWrapper:
        """
        Add an error handler to the current endpoint.

        Example:

            >>> wa = WhatsApp(...)
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...
            >>> def on_error(_: WhatsApp, req: FlowRequest):
            ...     logging.error("An error occurred: %s", req.data)
            >>> wa.add_flow_request_handler(
            ...     FlowRequestHandler(callback=feedback_flow_handler, endpoint="/feedback_flow")
            ... ).set_errors_handler(callback=on_error)
            ...

        Args:
            callback: The callback function to handle errors.

        Returns:
            The current instance.

        Raises:
            ValueError: If an error handler is already set for this endpoint.
        """
        if self._error_callback:
            raise ValueError("An error handler is already set for this endpoint.")
        self._wa._check_for_async_callback(callback)
        self._error_callback = callback
        return self

    def _get_callback(self, req: FlowRequest) -> _FlowRequestHandlerT:
        """Resolve the callback to use for the incoming request."""
        if req.has_error and self._error_callback:
            return self._error_callback
        for filters, callback in (
            *self._on_callbacks[(req.action, None)],  # No screen priority
            *self._on_callbacks[(req.action, req.screen)],
        ):
            if filters is None or filters.check_sync(self._wa, req):
                return callback
        return self._main_callback

    async def _get_callback_async(self, req: FlowRequest) -> _FlowRequestHandlerT:
        """Resolve the callback to use for the incoming request (async version)."""
        if req.has_error and self._error_callback:
            return self._error_callback
        for filters, callback in (
            *self._on_callbacks[(req.action, None)],  # No screen priority
            *self._on_callbacks[(req.action, req.screen)],
        ):
            if filters is None or await filters.check_async(self._wa, req):
                return callback
        return self._main_callback

    def handle(self, payload: EncryptedFlowRequestType) -> tuple[str, int]:
        """
        Handle the incoming flow request.

        Args:
            payload: The incoming request payload.

        Returns:
            A tuple containing the response data (json string) and the status code.
        """
        try:
            decrypted_request, aes_key, iv = self._decrypt_request(payload)
        except Exception:
            return "Decryption failed", FlowRequestCannotBeDecrypted.status_code

        if self._handle_health_check and decrypted_request["action"] == "ping":
            return self._encrypt_response(
                {
                    "version": decrypted_request["version"],
                    "data": {"status": "active"},
                },
                aes_key,
                iv,
            ), 200

        try:
            req = self._wa._flow_req_cls.from_dict(
                data=decrypted_request, raw_encrypted=payload
            )
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): Failed to construct FlowRequest from decrypted data: %s",
                self._endpoint,
                decrypted_request,
            )
            return "Failed to construct FlowRequest", 500

        return self._execute_callback(req, aes_key, iv)

    async def handle_async(self, payload: EncryptedFlowRequestType) -> tuple[str, int]:
        """
        Handle the incoming flow request asynchronously.

        Args:
            payload: The incoming request payload.

        Returns:
            A tuple containing the response data (json string) and the status code.
        """
        try:
            decrypted_request, aes_key, iv = self._decrypt_request(payload)
        except Exception:
            return "Decryption failed", FlowRequestCannotBeDecrypted.status_code

        if self._handle_health_check and decrypted_request["action"] == "ping":
            return self._encrypt_response(
                {
                    "version": decrypted_request["version"],
                    "data": {"status": "active"},
                },
                aes_key,
                iv,
            ), 200

        try:
            req = FlowRequest.from_dict(data=decrypted_request, raw_encrypted=payload)
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): Failed to construct FlowRequest from decrypted data: %s",
                self._endpoint,
                decrypted_request,
            )
            return "Failed to construct FlowRequest", 500

        return await self._execute_callback_async(req, aes_key, iv)

    def _decrypt_request(
        self, payload: EncryptedFlowRequestType
    ) -> tuple[dict, bytes, bytes]:
        decrypted_request, aes_key, iv = self._request_decryptor(
            payload["encrypted_flow_data"],
            payload["encrypted_aes_key"],
            payload["initial_vector"],
            self._private_key,
            self._private_key_password,
        )
        _logger.debug(
            "Flow Endpoint ('%s'): Received decrypted request: %s",
            self._endpoint,
            decrypted_request,
        )
        return decrypted_request, aes_key, iv

    def _encrypt_response(self, response: dict, aes_key: bytes, iv: bytes) -> str:
        return self._response_encryptor(response, aes_key, iv)

    def _execute_callback(
        self, req: FlowRequest, aes_key: bytes, iv: bytes
    ) -> tuple[str, int]:
        callback = self._get_callback(req)
        try:
            res = callback(self._wa, req)
            if isinstance(res, FlowResponseError):
                raise res
        except FlowResponseError as e:
            return self._encrypt_response(
                e.body or {"error": e.__class__.__name__},
                aes_key,
                iv,
            ), e.status_code
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): An error occurred while %s was handling a flow request",
                self._endpoint,
                callback.__name__,
            )
            return "An error occurred", 500

        if self._acknowledge_errors and req.has_error:
            return self._encrypt_response(
                {
                    "version": req.version,
                    "data": {
                        "acknowledged": True,
                    },
                },
                aes_key,
                iv,
            ), 200
        if not isinstance(res, (FlowResponse | dict)):
            raise TypeError(
                f"Flow endpoint ('{self._endpoint}') callback ('{callback.__name__}') must return a `FlowResponse`"
                f" or `dict`, not {type(res)}"
            )
        return self._encrypt_response(
            res.to_dict() if isinstance(res, FlowResponse) else res,
            aes_key,
            iv,
        ), 200

    async def _execute_callback_async(
        self, req: FlowRequest, aes_key: bytes, iv: bytes
    ) -> tuple[str, int]:
        callback = await self._get_callback_async(req)
        try:
            res = await callback(self._wa, req)
            if isinstance(res, FlowResponseError):
                raise res
        except FlowResponseError as e:
            return self._encrypt_response(
                e.body or {"error": e.__class__.__name__},
                aes_key,
                iv,
            ), e.status_code
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): An error occurred while %s was handling a flow request",
                self._endpoint,
                callback.__name__,
            )
            return "An error occurred", 500

        if self._acknowledge_errors and req.has_error:
            return self._encrypt_response(
                {
                    "version": req.version,
                    "data": {
                        "acknowledged": True,
                    },
                },
                aes_key,
                iv,
            ), 200
        if not isinstance(res, (FlowResponse | dict)):
            raise TypeError(
                f"Flow endpoint ('{self._endpoint}') callback ('{callback.__name__}') must return a `FlowResponse`"
                f" or `dict`, not {type(res)}"
            )
        return self._encrypt_response(
            res.to_dict() if isinstance(res, FlowResponse) else res,
            aes_key,
            iv,
        ), 200
