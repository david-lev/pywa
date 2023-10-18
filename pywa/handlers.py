"""
This module contains the handlers for incoming updates.
"""

from __future__ import annotations

__all__ = [
    "MessageHandler",
    "CallbackButtonHandler",
    "CallbackSelectionHandler",
    "RawUpdateHandler",
    "MessageStatusHandler",
    "TemplateStatusHandler",
]

import dataclasses
import abc
import functools
from typing import Callable, Any, TYPE_CHECKING, cast, TypeVar
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus, TemplateStatus
from pywa.types.base_update import BaseUpdate
from pywa.types.callback import CallbackData

if TYPE_CHECKING:
    from pywa.client import WhatsApp

CallbackDataFactoryT = TypeVar(
    'CallbackDataFactoryT',
    bound=(
            type[str] |
            type[CallbackData] |
            tuple[type[CallbackData | Any], ...] |
            list[type[CallbackData | Any], ...] |
            Callable[[str], Any]
    )
)
"""Type hint for the callback data factory."""


def _safe_issubclass(obj: type, base: type) -> bool:
    """Check if an obj is a subclass of another class without raising a TypeError."""
    try:
        return issubclass(obj, base)
    except TypeError:
        return False


def _resolve_callback_data_factory(
        factory: CallbackDataFactoryT
) -> tuple[CallbackDataFactoryT, Callable[[WhatsApp, Any], bool] | None]:
    """Internal function to resolve the callback data factory into a constractor and a filter."""
    clb_filter = None
    if isinstance(factory, (tuple, list)):  # The factory is a tuple|list of CallbackData subclasses or functions
        constractor = lambda data: (  # noqa
            factory.__class__(
                map(lambda fs: (fs[0].from_str if issubclass(fs[0], CallbackData) else fs[0])(fs[1]),  # noqa
                    zip(factory, data.split(CallbackData.__callback_sep__))))
        )
        if any((callback_datas := tuple(bool(issubclass(f, CallbackData)) for f in factory))):

            def clb_filter(_: WhatsApp, btn_or_sel: CallbackButton | CallbackSelection) -> bool:
                datas = btn_or_sel.data.split(CallbackData.__callback_sep__)
                if len(datas) != len(factory):
                    return False
                return all(
                    datas[i].startswith(
                        str(cast(CallbackData, factory[i]).__callback_id__) +
                        cast(CallbackData, factory[i]).__callback_data_sep__
                    )
                    for i, b in enumerate(callback_datas) if b
                )

    elif _safe_issubclass(factory, CallbackData):  # The factory is a single CallbackData subclass
        constractor = factory.from_str

        def clb_filter(_: WhatsApp, btn_or_sel: CallbackButton | CallbackSelection) -> bool:
            return len(btn_or_sel.data.split(CallbackData.__callback_sep__)) == 1 and \
                btn_or_sel.data.startswith(str(factory.__callback_id__) + factory.__callback_data_sep__)

    else:  # The factory is a function or custom type
        constractor = factory

    return constractor, clb_filter


def _call_callback_handler(
    handler: CallbackButtonHandler | CallbackSelectionHandler,
    wa: WhatsApp,
    clb_or_sel: CallbackButton | CallbackSelection
):
    """Internal function to call a callback handler."""
    if handler.factory_before_filters and handler.factory_filter is not None:
        if handler.factory_filter(wa, clb_or_sel):
            clb_or_sel = dataclasses.replace(clb_or_sel, data=handler.factory(clb_or_sel.data))
        else:
            return
    try:
        pass_filters = all((f(wa, clb_or_sel) for f in (
            *((handler.factory_filter,) if not handler.factory_before_filters
                and handler.factory_filter is not None else tuple()),
            *handler.filters
        )))
    except AttributeError as e:
        if not handler.factory_before_filters and isinstance(e.obj, str) and handler.factory is not str:
            raise TypeError("It seems like your filters tried to access a field of the callback data before the factory"
                            " was applied. Please set `factory_before_filters=True` in the handler constructor.") from e
        raise
    if pass_filters:
        if not handler.factory_before_filters and handler.factory is not str:
            clb_or_sel = dataclasses.replace(clb_or_sel, data=handler.factory(clb_or_sel.data))
        handler.handler(wa, clb_or_sel)


class Handler(abc.ABC):
    """Base class for all handlers."""

    @property
    @abc.abstractmethod
    def __field_name__(self) -> str:
        """
        The field name of the webhook update
        https://developers.facebook.com/docs/graph-api/webhooks/reference/whatsapp-business-account
        """

    @property
    @abc.abstractmethod
    def __update_constructor__(self) -> Callable[[WhatsApp, dict], BaseUpdate]:
        """The constructor to use to construct the update object from the webhook update dict."""

    def __init__(
            self,
            handler: Callable[[WhatsApp, Any], Any],
            *filters: Callable[[WhatsApp, Any], bool]
    ):
        """
        Initialize a new handler.
        """
        self.handler = handler
        self.filters = filters

    def __call__(self, wa: WhatsApp, data: Any):
        if all((f(wa, data) for f in self.filters)):
            self.handler(wa, data)

    def __hash__(self) -> int:
        """Return the hash of the handler field name."""
        return hash(self.__field_name__)

    @staticmethod
    @functools.cache
    def __fields_to_subclasses__() -> dict[str, Handler]:
        """Return a dict of all the subclasses of `Handler` with their field name as the key."""
        return {h.__field_name__: h for h in Handler.__subclasses__()}

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(handler={self.handler!r}, filters={self.filters!r})"

    def __repr__(self) -> str:
        return self.__str__()


class MessageHandler(Handler):
    """
    Handler for incoming :class:`pywa.types.Message`.

    - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_text_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageHandler(print_text_messages, fil.text))

    Args:
        handler: The handler function (gets the :class:`pywa.WhatsApp` instance and a :class:`pywa.types.Message` as
         arguments)
        *filters: The filters to apply to the handler (gets a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.Message` and returns a :class:`bool`)
    """
    __field_name__ = "messages:msg"
    __update_constructor__ = Message.from_update

    def __init__(
            self,
            handler: Callable[[WhatsApp, Message], Any],
            *filters: Callable[[WhatsApp, Message], bool]
    ):
        super().__init__(handler, *filters)


class CallbackButtonHandler(Handler):
    """
    Handler for callback buttons (User clicks on a :class:`pywa.types.Button`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_btn = lambda _, btn: print(btn)
        >>> wa.add_handlers(CallbackButtonHandler(print_btn, fil.callback.data_startswith('id:')))

    Args:
        handler: The handler function (gets the WhatsApp instance and the callback as arguments)
        *filters: The filters to apply to the handler (gets a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackButton` and returns a :class:`bool`)
        factory: The constructor/s to use to construct the callback data (default: :class:`str`. If the factory is a
         subclass of :class:`pywa.types.CallbackData`, a matching filter is automatically added).
        factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
         filters will get the callback data after the factory is applied).
    """
    __field_name__ = "messages:btn"
    __update_constructor__ = CallbackButton.from_update

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackButton], Any],
            *filters: Callable[[WhatsApp, CallbackButton], bool],
            factory: CallbackDataFactoryT = str,
            factory_before_filters: bool = False
    ):
        self.factory, self.factory_filter = _resolve_callback_data_factory(factory)
        self.factory_before_filters = factory_before_filters
        super().__init__(handler, *filters)

    def __call__(self, wa: WhatsApp, clb: CallbackButton):
        _call_callback_handler(self, wa, clb)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(handler={self.handler!r}, filters={self.filters!r}, factory={self.factory!r})"


class CallbackSelectionHandler(Handler):
    """
    Handler for callback selections (User selects an option from :class:`pywa.types.SectionList`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_selection = lambda _, sel: print(sel)
        >>> wa.add_handlers(CallbackSelectionHandler(print_selection, fil.callback.data_startswith('id:')))

    Args:
        handler: The handler function. (gets a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackSelection` as arguments)
        *filters: The filters to apply to the handler. (gets a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.CallbackSelection` and returns a :class:`bool`)
        factory: The constructor/s to use to construct the callback data (default: :class:`str`. If the factory is a
         subclass of :class:`pywa.types.CallbackData`, a matching filter is automatically added).
        factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
         filters will get the callback data after the factory is applied).
    """
    __field_name__ = "messages:sel"
    __update_constructor__ = CallbackSelection.from_update

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackSelection], Any],
            *filters: Callable[[WhatsApp, CallbackSelection], bool],
            factory: CallbackDataFactoryT = str,
            factory_before_filters: bool = False
    ):
        self.factory, self.factory_filter = _resolve_callback_data_factory(factory)
        self.factory_before_filters = factory_before_filters
        super().__init__(handler, *filters)

    def __call__(self, wa: WhatsApp, sel: CallbackSelection):
        _call_callback_handler(self, wa, sel)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(handler={self.handler!r}, filters={self.filters!r}, factory={self.factory!r})"


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
        handler: The handler function (gets a :class:`pywa.WhatsApp` instance and a :class:`pywa.types.MessageStatus` as
            arguments)
        *filters: The filters to apply to the handler (gets a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.MessageStatus` and returns a :class:`bool`)
    """
    __field_name__ = "messages:status"
    __update_constructor__ = MessageStatus.from_update

    def __init__(
            self,
            handler: Callable[[WhatsApp, MessageStatus], Any],
            *filters: Callable[[WhatsApp, MessageStatus], bool]
    ):
        super().__init__(handler, *filters)


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
        handler: The handler function (gets a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.TemplateStatus` as arguments)
        *filters: The filters to apply to the handler (gets a :class:`pywa.WhatsApp` instance and a
            :class:`pywa.types.TemplateStatus` and returns a :class:`bool`)
    """
    __field_name__ = "message_template_status_update"
    __update_constructor__ = TemplateStatus.from_update

    def __init__(
            self,
            handler: Callable[[WhatsApp, TemplateStatus], Any],
            *filters: Callable[[WhatsApp, TemplateStatus], bool]
    ):
        super().__init__(handler, *filters)


class RawUpdateHandler(Handler):
    """
    A raw update handler.

    - This handler will be called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
    - You can use the :func:`~pywa.client.WhatsApp.on_raw_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_updates = lambda _, data: print(data)
        >>> wa.add_handlers(RawUpdateHandler(print_updates))

    Args:
        handler: The handler function (gets a :class:`pywa.WhatsApp` instance and a :class:`dict` as arguments)
        *filters: The filters to apply to the handler (gets a :class:`pywa.WhatsApp` instance and a :class:`dict` and
            returns a :class:`bool`)
    """
    __field_name__ = "raw"
    __update_constructor__ = lambda _, data: data  # noqa

    def __init__(
            self,
            handler: Callable[[WhatsApp, dict], Any],
            *filters: Callable[[WhatsApp, dict], bool]
    ):
        super().__init__(handler, *filters)


class HandlerDecorators:
    def __init__(self):
        raise TypeError("This class cannot be instantiated.")

    def on_raw_update(
            self: WhatsApp, *filters: Callable[[WhatsApp, dict], bool]
    ) -> Callable[[Callable[[WhatsApp, dict], Any]], Callable[[WhatsApp, dict], Any]]:
        """
        Decorator to register a function as a handler for raw updates (:class:`dict`).

        - This handler is called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`RawUpdateHandler`.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_raw_update()
            ... def raw_update_handler(_: WhatsApp, update: dict):
            ...     print(update)

        Args:
            *filters: Filters to apply to the incoming updates (filters are function that take a :class:`pywa.WhatsApp`
             instance and the incoming update :class:`dict` and return a :class:`bool` if the update should be handled).
        """
        @functools.wraps(self.on_raw_update)
        def decorator(func: Callable[[WhatsApp, dict], Any]) -> Callable[[WhatsApp, dict], Any]:
            self.add_handlers(RawUpdateHandler(func, *filters))
            return func
        return decorator

    def on_message(
            self: WhatsApp, *filters: Callable[[WhatsApp, Message], bool]
    ) -> Callable[[Callable[[WhatsApp, Message], Any]], Callable[[WhatsApp, Message], Any]]:
        """
        Decorator to register a function as a handler for incoming :class:`pywa.types.Message` (User sends a message).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`MessageHandler`.

        Example:

            >>> from pywa.types import Button
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_message(fil.text.matches("Hello", "Hi", ignore_case=True))
            ... def hello_handler(_: WhatsApp, msg: Message):
            ...     msg.react("👋")
            ...     msg.reply_text(text="Hello from PyWa!", quote=True, buttons=[Button("Help", data="help")

        Args:
            *filters: Filters to apply to the incoming messages (filters are function that take a :class:`pywa.WhatsApp`
             instance and the incoming :class:`pywa.types.Message` and return a boolean).
        """
        @functools.wraps(self.on_message)
        def decorator(func: Callable[[WhatsApp, Message], Any]) -> Callable[[WhatsApp, Message], Any]:
            self.add_handlers(MessageHandler(func, *filters))
            return func
        return decorator

    def on_callback_button(
            self: WhatsApp,
            *filters: Callable[[WhatsApp, CallbackButton], bool],
            factory: CallbackDataFactoryT = str,
            factory_before_filters: bool = False
    ) -> Callable[[Callable[[WhatsApp, CallbackButton], Any]], Callable[[WhatsApp, CallbackButton], Any]]:
        """
        Decorator to register a function as a handler when a user clicks on a :class:`pywa.types.Button`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackButtonHandler`.

        Example:

            >>> from pywa.types import CallbackButton
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_button(fil.callback.data_matches("help"))
            ... def help_handler(_: WhatsApp, btn: CallbackButton):
            ...     btn.reply_text(text="What can I help you with?")

        Args:
            *filters: Filters to apply to the incoming callback button presses (filters are function that take a
             :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.CallbackButton` and return :class:`bool`).
            factory: The constructor/s to use for the callback data (default: :class:`str`. If the factory is a
             subclass of :class:`pywa.types.CallbackData`, a matching filter is automatically added).
            factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
             filters will get the callback data after the factory is applied).
        """
        @functools.wraps(self.on_callback_button)
        def decorator(func: Callable[[WhatsApp, CallbackButton], Any]) -> Callable[[WhatsApp, CallbackButton], Any]:
            self.add_handlers(
                CallbackButtonHandler(
                    func, *filters, factory=factory, factory_before_filters=factory_before_filters
                )
            )
            return func
        return decorator

    def on_callback_selection(
            self: WhatsApp,
            *filters: Callable[[WhatsApp, CallbackSelection], bool],
            factory: CallbackDataFactoryT = str,
            factory_before_filters: bool = False
    ) -> Callable[[Callable[[WhatsApp, CallbackSelection], Any]], Callable[[WhatsApp, CallbackSelection], Any]]:
        """
        Decorator to register a function as a handler when a user selects an option from a :class:`pywa.types.SectionList`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`CallbackSelectionHandler`.

        Example:

            >>> from pywa.types import CallbackSelection
            >>> from pywa import filters as fil
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_selection(fil.callback.data_startswith("id:"))
            ... def id_handler(_: WhatsApp, sel: CallbackSelection):
            ...     sel.reply_text(text=f"Your ID is {sel.data.split(':', 1)[1]}")

        Args:
            *filters: Filters to apply to the incoming callback selections (filters are function that take a
             :class:`pywa.WhatsApp` instance and the incoming :class:`pywa.types.CallbackSelection` and return :class:`bool`).
            factory: The constructor/s to use for the callback data (default: :class:`str`. If the factory is a
             subclass of :class:`pywa.types.CallbackData`, a matching filter is automatically added).
            factory_before_filters: Whether to apply the factory before the filters (default: ``False``. If ``True``, the
             filters will get the callback data after the factory is applied).
        """
        @functools.wraps(self.on_callback_selection)
        def decorator(
                func: Callable[[WhatsApp, CallbackSelection], Any]
        ) -> Callable[[WhatsApp, CallbackSelection], Any]:
            self.add_handlers(
                CallbackSelectionHandler(
                    func, *filters, factory=factory, factory_before_filters=factory_before_filters
                )
            )
            return func
        return decorator

    def on_message_status(
            self: WhatsApp, *filters: Callable[[WhatsApp, MessageStatus], bool]
    ) -> Callable[[Callable[[WhatsApp, MessageStatus], Any]], Callable[[WhatsApp, MessageStatus], Any]]:
        """
        Decorator to register a function as a handler for incoming message status changes (Message is sent, delivered,
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
        """
        @functools.wraps(self.on_message_status)
        def decorator(func: Callable[[WhatsApp, MessageStatus], Any]) -> Callable[[WhatsApp, MessageStatus], Any]:
            self.add_handlers(MessageStatusHandler(func, *filters))
            return func

        return decorator

    def on_template_status(
            self: WhatsApp, *filters: Callable[[WhatsApp, TemplateStatus], bool]
    ) -> Callable[[Callable[[WhatsApp, TemplateStatus], Any]], Callable[[WhatsApp, TemplateStatus], Any]]:
        """
        Decorator to register a function as a handler for :class:`pywa.types.TemplateStatus` updates (Template message
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
        """
        @functools.wraps(self.on_template_status)
        def decorator(func: Callable[[WhatsApp, TemplateStatus], Any]) -> Callable[[WhatsApp, TemplateStatus], Any]:
            self.add_handlers(TemplateStatusHandler(func, *filters))
            return func
        return decorator
