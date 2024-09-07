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
import asyncio
import collections
import dataclasses
import functools
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, cast, TypeAlias, Awaitable, TypedDict

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


class _EncryptedFlowRequestType(TypedDict):
    """Encrypted Flow Request Type."""

    encrypted_flow_data: str
    encrypted_aes_key: str
    initial_vector: str


_logger = logging.getLogger(__name__)


def _safe_issubclass(obj: type, base: type) -> bool:
    """Check if an obj is a subclass of another class without raising a TypeError."""
    try:
        return issubclass(obj, base)
    except TypeError:
        return False


def _resolve_factory(
    factory: _CallbackDataFactoryT,
    field_name: str,
) -> tuple[_CallbackDataFactoryT, Callable[[WhatsApp, Any], bool] | None]:
    """Internal function to resolve the callback data factory into a constractor and a filter."""
    factory_filter = None
    if isinstance(
        factory, (tuple, list)
    ):  # The factory is a tuple|list of CallbackData subclasses or functions

        async def constractor(data: str) -> tuple[Any, ...] | list[Any, ...]:
            objs = []
            for fact, split in zip(factory, data.split(CallbackData.__callback_sep__)):
                if _safe_issubclass(fact, CallbackData):
                    objs.append(fact.from_str(split))
                else:
                    objs.append(
                        await fact(split)
                        if inspect.iscoroutinefunction(fact)
                        else fact(split)
                    )
            return factory.__class__(objs)

        if any(
            (
                callback_datas := tuple(
                    _safe_issubclass(f, CallbackData) for f in factory
                )
            )
        ):

            def factory_filter(
                _: WhatsApp, update: CallbackButton | CallbackSelection | MessageStatus
            ) -> bool:
                raw_data = getattr(update, field_name)
                if raw_data is None:
                    return False
                datas = raw_data.split(CallbackData.__callback_sep__)
                if len(datas) != len(factory):
                    return False
                return all(
                    datas[i].startswith(
                        str(cast(CallbackData, factory[i]).__callback_id__)
                        + cast(CallbackData, factory[i]).__callback_data_sep__
                    )
                    for i, b in enumerate(callback_datas)
                    if b
                )

    elif _safe_issubclass(
        factory, CallbackData
    ):  # The factory is a single CallbackData subclass
        constractor = factory.from_str

        def factory_filter(
            _: WhatsApp, update: CallbackButton | CallbackSelection | MessageStatus
        ) -> bool:
            raw_data = getattr(update, field_name)
            if raw_data is None:
                return False
            return len(
                raw_data.split(CallbackData.__callback_sep__)
            ) == 1 and raw_data.startswith(
                str(factory.__callback_id__) + factory.__callback_data_sep__
            )

    else:  # The factory is a function or custom type
        constractor = factory

    return constractor, factory_filter


async def _get_factored_update(
    handler: _FactoryHandler,
    wa: WhatsApp,
    update: CallbackButton | CallbackSelection | MessageStatus,
    field_name: str,
) -> CallbackButton | CallbackSelection | MessageStatus | None:
    """Internal function to get the factored update."""
    if handler.factory_before_filters and handler.factory_filter is not None:
        if handler.factory_filter(wa, update):
            data = getattr(update, field_name)
            if data is None:
                return
            factorized_data = (
                await handler.factory(data)
                if inspect.iscoroutinefunction(handler.factory)
                else handler.factory(data)
            )
            update = dataclasses.replace(update, **{field_name: factorized_data})
        else:
            return
    try:
        for f in (
            *(
                (handler.factory_filter,)
                if not handler.factory_before_filters
                and handler.factory_filter is not None
                else tuple()
            ),
            *handler.filters,
        ):
            if not (
                await f(wa, update) if inspect.iscoroutinefunction(f) else f(wa, update)
            ):
                return
    except AttributeError as e:
        if (
            not handler.factory_before_filters
            and isinstance(e.obj, str)
            and handler.factory is not str
        ):
            raise AttributeError(
                "It seems like your filters tried to access a field of the callback data before the factory"
                " was applied. Please set `factory_before_filters=True` in the callback constructor."
            ) from e
        raise

    if not handler.factory_before_filters and handler.factory is not str:
        data = getattr(update, field_name)
        if data is None:
            return
        factorized_data = (
            await handler.factory(data)
            if inspect.iscoroutinefunction(handler.factory)
            else handler.factory(data)
        )
        update = dataclasses.replace(update, **{field_name: factorized_data})
    return update


class Handler(abc.ABC):
    """Base class for all handlers."""

    @property
    @abc.abstractmethod
    def _field_name(self) -> str | None:
        """
        The field name of the webhook update
        https://developers.facebook.com/docs/graph-api/webhooks/reference/whatsapp-business-account
        """

    def __init__(
        self,
        callback: Callable[[WhatsApp, Any], Any],
        *filters: Callable[[WhatsApp, Any], bool | Awaitable[bool]],
        priority: int,
    ):
        """
        Initialize a new callback.
        """
        self.callback = callback
        self.filters = filters
        self.priority = priority

    async def handle(self, wa: WhatsApp, data: Any) -> bool:
        for f in self.filters:
            if not (
                await f(wa, data) if inspect.iscoroutinefunction(f) else f(wa, data)
            ):
                return False

        await self.callback(wa, data) if inspect.iscoroutinefunction(
            self.callback
        ) else self.callback(wa, data)
        return True

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
        return f"{self.__class__.__name__}({self.callback=!r}, {self.filters=!r}, {self.priority=})"

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
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = "messages"

    def __init__(
        self,
        callback: Callable[[WhatsApp, Message], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, Message], bool | Awaitable[bool]],
        priority: int = 0,
    ):
        super().__init__(callback, *filters, priority=priority)


class _FactoryHandler(Handler):
    """Base class for handlers that use a factory to construct the callback data."""

    _field_name = "messages"
    _data_field: str

    def __init__(
        self,
        callback: Callable[[WhatsApp, Any], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, Any], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ):
        (
            self.factory,
            self.factory_filter,
        ) = _resolve_factory(factory, self._data_field)
        self.factory_before_filters = factory_before_filters
        super().__init__(callback, *filters, priority=priority)

    async def handle(self, wa: WhatsApp, data: Any) -> bool:
        update = await _get_factored_update(self, wa, data, self._data_field)
        if update is not None:
            await self.callback(wa, update) if inspect.iscoroutinefunction(
                self.callback
            ) else self.callback(wa, update)
            return True
        return False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.callback=!r}, {self.filters=!r}, {self.factory=!r}, {self.priority=!r})"


class CallbackButtonHandler(_FactoryHandler):
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
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "data"

    def __init__(
        self,
        callback: Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, CallbackButton], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ):
        super().__init__(
            callback,
            *filters,
            factory=factory,
            factory_before_filters=factory_before_filters,
            priority=priority,
        )


class CallbackSelectionHandler(_FactoryHandler):
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
         filters will get the callback data after the factory is applied)
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "data"

    def __init__(
        self,
        callback: Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, CallbackSelection], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ):
        super().__init__(
            callback,
            *filters,
            factory=factory,
            factory_before_filters=factory_before_filters,
            priority=priority,
        )


class MessageStatusHandler(_FactoryHandler):
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
            filters will get the tracker data after the factory is applied)
        priority: The priority of the handler (default: ``0``)
    """

    _data_field = "tracker"

    def __init__(
        self,
        callback: Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, MessageStatus], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ):
        super().__init__(
            callback,
            *filters,
            factory=factory,
            factory_before_filters=factory_before_filters,
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
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.ChatOpened` and returns a :class:`bool`)
        priority: The priority of the handler (default: ``0``)

    """

    _field_name = "messages"

    def __init__(
        self,
        callback: Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, ChatOpened], bool | Awaitable[bool]],
        priority: int = 0,
    ):
        super().__init__(callback, *filters, priority=priority)


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
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = "message_template_status_update"

    def __init__(
        self,
        callback: Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, TemplateStatus], bool | Awaitable[bool]],
        priority: int = 0,
    ):
        super().__init__(callback, *filters, priority=priority)


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
        *filters: The filters to apply to the handler (Takes a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.FlowCompletion` and returns a :class:`bool`)
        priority: The priority of the handler (default: ``0``)

    """

    _field_name = "messages"

    def __init__(
        self,
        callback: Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, FlowCompletion], bool | Awaitable[bool]],
        priority: int = 0,
    ):
        super().__init__(callback, *filters, priority=priority)


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
        priority: The priority of the handler (default: ``0``)
    """

    _field_name = None

    def __init__(
        self,
        callback: Callable[[WhatsApp, dict], Any | Awaitable[Any]],
        *filters: Callable[[WhatsApp, dict], bool | Awaitable[bool]],
        priority: int = 0,
    ):
        super().__init__(callback, *filters, priority=priority)


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


class HandlerDecorators:
    """This class is used by the :class:`WhatsApp` client to register handlers using decorators."""

    def __init__(self: WhatsApp):
        raise TypeError("This class cannot be instantiated.")

    def on_raw_update(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, dict], bool | Awaitable[bool]],
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, dict], Any | Awaitable[Any]]],
        Callable[[WhatsApp, dict], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for raw updates (:class:`dict`).

        - This callback is called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`RawUpdateHandler`.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_raw_update()
            ... def raw_update_handler(_: WhatsApp, update: dict):
            ...     print(update)

        Args:
            *filters: Filters to apply to the incoming updates (filters are function that take a :class:`pywa.WhatsApp`
             instance and the incoming update as :class:`dict` and return a :class:`bool` if the update should be handled).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, dict], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, dict], Any | Awaitable[Any]]:
            self.add_handlers(RawUpdateHandler(callback, *filters, priority=priority))
            return callback

        return decorator

    def on_message(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, Message], bool | Awaitable[bool]],
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, Message], Any | Awaitable[Any]]],
        Callable[[WhatsApp, Message], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for incoming :class:`pywa.types.Message` (User sends a message).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`MessageHandler`.

        Example:

            >>> from pywa.types import Button
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_message(fil.matches("Hello", "Hi", ignore_case=True))
            ... def hello_handler(_: WhatsApp, msg: Message):
            ...     msg.react("👋")
            ...     msg.reply_text(text="Hello from PyWa!", quote=True, buttons=[Button("Help", data="help")

        Args:
            *filters: Filters to apply to the incoming messages (filters are function that take a :class:`pywa.WhatsApp`
             instance and the incoming :class:`pywa.types.Message` and return a boolean).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, Message], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, Message], Any | Awaitable[Any]]:
            self.add_handlers(MessageHandler(callback, *filters, priority=priority))
            return callback

        return decorator

    def on_callback_button(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, CallbackButton], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]]],
        Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback when a user clicks on a :class:`pywa.types.Button`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackButtonHandler`.

        Example:

            >>> from pywa.types import CallbackButton
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_button(fil.matches("help"))
            ... def help_handler(_: WhatsApp, btn: CallbackButton):
            ...     btn.reply_text(text="What can I help you with?")

        Args:
            *filters: Filters to apply to the incoming callback button presses (filters are function that take a
             :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.CallbackButton` and return :class:`bool`).
            factory: The constructor/s to use for the callback data (default: :class:`str`. If the factory is a
             subclass of :class:`CallbackData`, a matching filter is automatically added).
            factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
             filters will get the callback data after the factory is applied).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, CallbackButton], Any | Awaitable[Any]]:
            self.add_handlers(
                CallbackButtonHandler(
                    callback,
                    *filters,
                    factory=factory,
                    factory_before_filters=factory_before_filters,
                    priority=priority,
                )
            )
            return callback

        return decorator

    def on_callback_selection(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, CallbackSelection], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]]],
        Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback when a user selects an option from a :class:`pywa.types.SectionList`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackSelectionHandler`.

        Example:

            >>> from pywa.types import CallbackSelection
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_selection(fil.startswith("id:"))
            ... def id_handler(_: WhatsApp, sel: CallbackSelection):
            ...     sel.reply_text(text=f"Your ID is {sel.data.split(':', 1)[1]}")

        Args:
            *filters: Filters to apply to the incoming callback selections (filters are function that take a
             :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.CallbackSelection` and return :class:`bool`).
            factory: The constructor/s to use for the callback data (default: :class:`str`. If the factory is a
             subclass of :class:`CallbackData`, a matching filter is automatically added).
            factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
             filters will get the callback data after the factory is applied).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, CallbackSelection], Any | Awaitable[Any]]:
            self.add_handlers(
                CallbackSelectionHandler(
                    callback,
                    *filters,
                    factory=factory,
                    factory_before_filters=factory_before_filters,
                    priority=priority,
                )
            )
            return callback

        return decorator

    def on_message_status(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, MessageStatus], bool | Awaitable[bool]],
        factory: _CallbackDataFactoryT = str,
        factory_before_filters: bool = False,
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]]],
        Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for incoming message status changes (Message is sent, delivered,
        read, failed, etc...).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`MessageStatusHandler`.

        **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

        Example:

            >>> from pywa.types import MessageStatus
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_message_status(fil.message_status.failed)
            ... def delivered_handler(client: WhatsApp, status: MessageStatus):
            ...     print(f"Message {status.id} failed to send to {status.from_user.wa_id}: {status.error.message})


        Args:
            *filters: Filters to apply to the incoming message status changes (filters are function that take a
             :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.MessageStatus` and return :class:`bool`).
            factory: The constructor/s to use for the tracker data (default: :class:`str`. If the factory is a
                subclass of :class:`CallbackData`, a matching filter is automatically added).
            factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
                filters will get the tracker data after the factory is applied).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, MessageStatus], Any | Awaitable[Any]]:
            self.add_handlers(
                MessageStatusHandler(
                    callback,
                    *filters,
                    factory=factory,
                    factory_before_filters=factory_before_filters,
                    priority=priority,
                )
            )
            return callback

        return decorator

    def on_chat_opened(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, ChatOpened], bool | Awaitable[bool]],
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]]],
        Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for incoming chat opened (User opens a chat).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`ChatOpenedHandler`.

        Example:

            >>> from pywa.types import ChatOpened
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_chat_opened()
            ... def chat_opened_handler(client: WhatsApp, chat_opened: ChatOpened):
            ...     print(f"The user {chat_opened.from_user.wa_id} just opened a chat with us!")

        Args:
            *filters: Filters to apply to the incoming chat opened (filters are function that take a
                :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.ChatOpened` and return :class:`bool`).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, ChatOpened], Any | Awaitable[Any]]:
            self.add_handlers(ChatOpenedHandler(callback, *filters, priority=priority))
            return callback

        return decorator

    def on_template_status(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, TemplateStatus], bool | Awaitable[bool]],
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]]],
        Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for :class:`pywa.types.TemplateStatus` updates (Template message
        is approved, rejected etc...).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`TemplateStatusHandler`.

        Example:

            >>> from pywa.types import TemplateStatus
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_status(fil.template_status.on_event(TemplateStatus.TemplateEvent.APPROVED))
            ... def approved_handler(client: WhatsApp, status: TemplateStatus):
            ...     print(f"Template {status.message_template_name} just got approved!")

        Args:
            *filters: Filters to apply to the incoming template status changes (filters are function that take a
                :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.TemplateStatus` and return :class:`bool`).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, TemplateStatus], Any | Awaitable[Any]]:
            self.add_handlers(
                TemplateStatusHandler(callback, *filters, priority=priority)
            )
            return callback

        return decorator

    def on_flow_completion(
        self: WhatsApp,
        *filters: Callable[[WhatsApp, FlowCompletion], bool | Awaitable[bool]],
        priority: int = 0,
    ) -> Callable[
        [Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]]],
        Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]],
    ]:
        """
        Decorator to register a function as a callback for :class:`pywa.types.FlowCompletion` updates (Flow is completed).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`FlowCompletionHandler`.

        Example:

            >>> from pywa.types import FlowCompletion
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_completion()
            ... def flow_handler(client: WhatsApp, flow: FlowCompletion):
            ...     print(f"Flow {flow.token} just got completed!. Flow data: {flow.response}")

        Args:
            *filters: Filters to apply to the incoming flow completion (filters are function that take a
                :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.FlowCompletion` and return :class:`bool`).
            priority: The priority of the handler (default: ``0``).
        """

        def decorator(
            callback: Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]],
        ) -> Callable[[WhatsApp, FlowCompletion], Any | Awaitable[Any]]:
            self.add_handlers(
                FlowCompletionHandler(callback, *filters, priority=priority)
            )
            return callback

        return decorator

    def on_flow_request(
        self: WhatsApp,
        endpoint: str,
        *,
        acknowledge_errors: bool = True,
        handle_health_check: bool = True,
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ) -> Callable[
        [_FlowRequestHandlerT],
        FlowRequestCallbackWrapper,
    ]:
        """
        Decorator to register a function to handle and respond to incoming Flow Data Exchange requests.

        Example:

            >>> from pywa import WhatsApp
            >>> wa = WhatsApp(business_private_key='...', ...)
            >>> @wa.on_flow_request('/feedback_flow')
            ... def feedback_flow_handler(_: WhatsApp, flow: FlowRequest) -> FlowResponse:
            ...     return FlowResponse(
            ...         version=flow.version,
            ...         screen="SURVEY",
            ...         data={
            ...             "default_text": "Please rate your experience with our service",
            ...             "text_required": True
            ...         }
            ...     )

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
        ) -> FlowRequestCallbackWrapper:
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
        self._main_callback = callback
        self._error_callback: _FlowRequestHandlerT | None = None
        self._on_callbacks: dict[
            tuple[FlowRequestActionType | str, str | None],
            list[
                tuple[
                    Callable[["WhatsApp", dict | None], bool | Awaitable[bool]] | None,
                    _FlowRequestHandlerT,
                ]
            ],
        ] = collections.defaultdict(
            list
        )  # {(action, screen?): [(data_filter?, callback)]}
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
        data_filter: Callable[[WhatsApp, dict | None], bool | Awaitable[bool]]
        | None = None,
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
            >>> @feedback_flow_handler.on(..., data_filter=lambda _, data: data.get("rating") == 5)
            >>> def on_rating_5(_: WhatsApp, req: FlowRequest):
            ...     ...

        Args:
            action: The action type to listen to.
            screen: The screen ID to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            data_filter: A filter function to apply to the incoming data.

        Returns:
            The function itself.
        """

        def decorator(callback: _FlowRequestHandlerT):
            self.add_handler(
                callback=callback, action=action, screen=screen, data_filter=data_filter
            )
            return callback

        return decorator

    def on_errors(self) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add an error handler to the current endpoint.

        - Shortcut for :func:`~pywa.client.FlowRequestCallbackWrapper.set_errors_handler`.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...
            >>> @feedback_flow_handler.on_errors()
            >>> def on_error(_: WhatsApp, req: FlowRequest):
            ...     logging.error("An error occurred: %s", req.data)

        Returns:
            The function itself.
        """

        def decorator(callback: _FlowRequestHandlerT):
            self.set_errors_handler(callback)
            return callback

        return decorator

    def add_handler(
        self,
        *,
        callback: _FlowRequestHandlerT,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        data_filter: Callable[[WhatsApp, dict | None], bool | Awaitable[bool]]
        | None = None,
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
            data_filter: A filter function to apply to the incoming data.

        Returns:
            The current instance.
        """
        self._on_callbacks[
            (action, screen.id if isinstance(screen, Screen) else screen)
        ].append((data_filter, callback))
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
        self._error_callback = callback
        return self

    async def _get_callback(self, req: FlowRequest) -> _FlowRequestHandlerT:
        """Resolve the callback to use for the incoming request."""
        if req.has_error and self._error_callback:
            return self._error_callback
        for data_filter, callback in (
            *self._on_callbacks[(req.action, None)],  # No screen priority
            *self._on_callbacks[(req.action, req.screen)],
        ):
            if data_filter is None or (
                await data_filter(self._wa, req.data)
                if asyncio.iscoroutinefunction(data_filter)
                else data_filter(self._wa, req.data)
            ):
                return callback
        return self._main_callback

    async def handle(self, payload: _EncryptedFlowRequestType) -> tuple[str, int]:
        """
        Handle the incoming flow request.

        - This method should be called when using a custom server.

        Example:

            .. code-block:: python
                :emphasize-lines: 4, 14
                :linenos:

                from aiohttp import web
                from pywa import WhatsApp, flows

                wa = WhatsApp(..., server=None, business_private_key="...", business_private_key_password="...")

                async def my_flow_callback(wa: WhatsApp, request: flows.FlowRequest) -> flows.FlowResponse:
                    ...

                flow_handler = wa.get_flow_request_handler(
                    endpoint="/flow",
                    callback=my_flow_callback,
                )

                async def my_flow_endpoint(req: web.Request) -> web.Response:
                    response, status_code = await flow_handler.handle(await req.json())
                    return web.Response(text=response, status=status_code)

                app = web.Application()
                app.add_routes([web.post("/flow", my_flow_endpoint)])

                if __name__ == "__main__":
                    web.run_app(app, port=...)

        Args:
            payload: The incoming request payload.

        Returns:
            A tuple containing the response data (json string) and the status code.
        """
        return await self(payload)

    async def __call__(self, payload: _EncryptedFlowRequestType) -> tuple[str, int]:
        """
        Handle the incoming request internally.

        - This method is called automatically by pywa, or manually when using custom server.

        Args:
            payload: The incoming request payload.

        Returns:
            A tuple containing the response data and the status code.
        """
        try:
            decrypted_request, aes_key, iv = self._request_decryptor(
                payload["encrypted_flow_data"],
                payload["encrypted_aes_key"],
                payload["initial_vector"],
                self._private_key,
                self._private_key_password,
            )
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): Decryption failed for payload: %s",
                self._endpoint,
                payload,
            )
            return "Decryption failed", FlowRequestCannotBeDecrypted.status_code
        _logger.debug(
            "Flow Endpoint ('%s'): Received decrypted request: %s",
            self._endpoint,
            decrypted_request,
        )
        if self._handle_health_check and decrypted_request["action"] == "ping":
            return self._response_encryptor(
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

        callback = await self._get_callback(req)
        try:
            res = (
                await callback(self._wa, req)
                if asyncio.iscoroutinefunction(callback)
                else callback(self._wa, req)
            )
            if isinstance(res, FlowResponseError):
                raise res
        except FlowResponseError as e:
            return (
                self._response_encryptor(
                    e.body or {"error": e.__class__.__name__},
                    aes_key,
                    iv,
                ),
                e.status_code,
            )
        except Exception:
            _logger.exception(
                "Flow Endpoint ('%s'): An error occurred while %s was handling a flow request",
                self._endpoint,
                callback.__name__,
            )
            return "An error occurred", 500

        if self._acknowledge_errors and req.has_error:
            return self._response_encryptor(
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
        return self._response_encryptor(
            res.to_dict() if isinstance(res, FlowResponse) else res,
            aes_key,
            iv,
        ), 200
