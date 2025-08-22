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
    "TemplateStatusUpdateHandler",
    "TemplateCategoryUpdateHandler",
    "TemplateQualityUpdateHandler",
    "TemplateComponentsUpdateHandler",
    "FlowCompletionHandler",
    "FlowRequestHandler",
    "ChatOpenedHandler",
    "PhoneNumberChangeHandler",
    "IdentityChangeHandler",
    "CallConnectHandler",
    "CallTerminateHandler",
    "CallStatusHandler",
    "CallPermissionUpdateHandler",
    "UserMarketingPreferencesHandler",
]

import abc
import collections
import dataclasses
import functools
import logging
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    cast,
    TypeAlias,
    Awaitable,
    TypedDict,
    Generic,
    TypeVar,
)

from . import utils
from .filters import Filter, new as new_filter
from .types import (
    CallbackButton,
    CallbackSelection,
    Message,
    MessageStatus,
    TemplateStatusUpdate,
    TemplateQualityUpdate,
    TemplateComponentsUpdate,
    TemplateCategoryUpdate,
    UserMarketingPreferences,
    FlowRequest,
    FlowResponse,
    ChatOpened,
    CallbackData,
    FlowButton,
    FlowActionType,
    CallConnect,
    CallTerminate,
    CallStatus,
    PhoneNumberChange,
    IdentityChange,
    CallPermissionUpdate,
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
    FlowResponse | dict | None | Awaitable[FlowResponse | dict | None],
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
_TemplateStatusUpdateCallback: TypeAlias = Callable[
    ["WhatsApp", TemplateStatusUpdate], Any | Awaitable[Any]
]
_TemplateCategoryUpdateCallback: TypeAlias = Callable[
    ["WhatsApp", TemplateCategoryUpdate], Any | Awaitable[Any]
]
_TemplateQualityUpdateCallback: TypeAlias = Callable[
    ["WhatsApp", TemplateQualityUpdate], Any | Awaitable[Any]
]
_TemplateComponentsUpdateCallback: TypeAlias = Callable[
    ["WhatsApp", TemplateComponentsUpdate], Any | Awaitable[Any]
]
_FlowCompletionCallback: TypeAlias = Callable[
    ["WhatsApp", FlowCompletion], Any | Awaitable[Any]
]
_CallConnectCallback: TypeAlias = Callable[
    ["WhatsApp", CallConnect], Any | Awaitable[Any]
]
_CallTerminateCallback: TypeAlias = Callable[
    ["WhatsApp", CallTerminate], Any | Awaitable[Any]
]
_CallStatusCallback: TypeAlias = Callable[
    ["WhatsApp", CallStatus], Any | Awaitable[Any]
]
_CallPermissionUpdateCallback: TypeAlias = Callable[
    ["WhatsApp", "CallPermissionUpdate"],
    Any | Awaitable[Any],
]
_UserMarketingPreferencesCallback: TypeAlias = Callable[
    ["WhatsApp", "UserMarketingPreferences"],
    Any | Awaitable[Any],
]
_PhoneNumberChangeCallback: TypeAlias = Callable[
    ["WhatsApp", "PhoneNumberChange"],
    Any | Awaitable[Any],
]
_IdentityChangeCallback: TypeAlias = Callable[
    ["WhatsApp", "IdentityChange"],
    Any | Awaitable[Any],
]


class EncryptedFlowRequestType(TypedDict):
    """Encrypted Flow Request Type."""

    encrypted_flow_data: str
    encrypted_aes_key: str
    initial_vector: str


_logger = logging.getLogger(__name__)

_FactorySupported: TypeAlias = (
    CallbackButton | CallbackSelection | MessageStatus | CallStatus
)

_UpdateType = TypeVar("_UpdateType")


class Handler(Generic[_UpdateType]):
    """Base class for all handlers."""

    _update: type[_UpdateType] | None
    """The update this handler should handle"""

    def __init__(
        self,
        callback: Callable[[WhatsApp, _UpdateType], Any | Awaitable[Any]],
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

    def check(self, wa: WhatsApp, update: _UpdateType) -> bool:
        return self._filters is None or self._filters.check_sync(wa, update)

    def handle(self, wa: WhatsApp, update: _UpdateType) -> bool:
        if not self.check(wa, update):
            return False
        self._callback(wa, update)
        return True

    async def acheck(self, wa: WhatsApp, update: _UpdateType) -> bool:
        return self._filters is None or await self._filters.check_async(wa, update)

    async def ahandle(self, wa: WhatsApp, update: _UpdateType) -> bool:
        if not await self.acheck(wa, update):
            return False
        await self._callback(wa, update) if self._is_async_callback else self._callback(
            wa, update
        )
        return True

    @staticmethod
    @functools.cache
    def _handled_fields() -> dict[str, type[Handler]]:
        """
        Return a dict of all the subclasses of `Handler` with their update field name as the key.
        (e.g. `{'messages': MessageHandler}, 'calls': CallConnect}`)

        **IMPORTANT:** This function is for internal use only, DO NOT USE IT to get the available handlers
        (use ``Handler.__subclasses__()`` instead).

        **IMPORTANT:** This function is cached, so if you subclass ``Handler`` after calling this function, the new class
        will not be included in the returned dict.
        """
        return cast(
            dict[str, type[Handler]],
            {
                h._update._webhook_field: h
                for h in Handler.__subclasses__()
                if h._update is not None
            },
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(callback={self._callback}, filters={self._filters}, priority={self._priority})"

    def __str__(self) -> str:
        return self.__repr__()


class MessageHandler(Handler[Message]):
    """
    Handler for :class:`~pywa.types.Message` updates (Text, media, etc...).

    - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_text_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageHandler(print_text_messages, filters.text))

    Args:
        callback: The callback function (Takes the :class:`~pywa.client.WhatsApp` client instance and a :class:`~pywa.types.Message` as positional arguments).
        filters: The filters to apply to the callback
        priority: The priority of the handler (default: ``0``)
    """

    _update = Message

    def __init__(
        self,
        callback: _MessageCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class _FactoryHandler(Generic[_UpdateType], Handler[_UpdateType]):
    """Base class for handlers that use a factory to construct the callback data."""

    _update = None
    _data_field: str

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


class CallbackButtonHandler(_FactoryHandler[CallbackButton]):
    """
    Handler for :class:`~pywa.types.CallbackButton` updates (user clicks on a :class:`~pywa.types.callback.Button` or :class:`~pywa.types.templates.QuickReplyButton`).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_btn = lambda _, btn: print(btn)
        >>> wa.add_handlers(CallbackButtonHandler(print_btn, filters.startswith('id:')))

    Args:
        callback: The callback function. (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.CallbackButton` as positional arguments)
        filters: The filters to apply to the handler
        factory: The :class:`~pywa.types.callback.CallbackData` constructor to use to construct the callback data.
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallbackButton
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


class CallbackSelectionHandler(_FactoryHandler[CallbackSelection]):
    """
    Handler for :class:`~pywa.types.CallbackSelection` updates (user selects an :class:`~pywa.types.callback.SectionRow` from a :class:`~pywa.types.callback.SectionList`.).

    - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters
        >>> wa = WhatsApp(...)
        >>> print_selection = lambda _, sel: print(sel)
        >>> wa.add_handlers(CallbackSelectionHandler(print_selection, filters.startswith('id:')))

    Args:
        callback: The callback function. (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.callback.CallbackSelection` as positional arguments)
        filters: The filters to apply to the handler
        factory: The :class:`~pywa.types.callback.CallbackData` constructor to use to construct the callback data.
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallbackSelection
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


class MessageStatusHandler(_FactoryHandler[MessageStatus]):
    """
    Handler for :class:`~pywa.types.message_status.MessageStatus` updates (Message status updates, e.g. ``sent``, ``delivered``, ``read``).

    - You can use the :func:`~pywa.client.WhatsApp.on_message_status` decorator to register a handler for this type.

    **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

    Example:

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)
        >>> print_failed_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageStatusHandler(print_failed_messages, filters.failed))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.message_status.MessageStatus` as positional arguments).
        filters: The filters to apply to the handler
        factory: The :class:`~pywa.types.callback.CallbackData` constructor to use to construct the ``tracker`` data.
        priority: The priority of the handler (default: ``0``)
    """

    _update = MessageStatus
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


class ChatOpenedHandler(Handler[ChatOpened]):
    """
    Handler for :class:`~pywa.types.ChatOpened` updates (Chat is opened).

    - You can use the :func:`~pywa.client.WhatsApp.on_chat_opened` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_chat_opened = lambda _, msg: print(msg)
        >>> wa.add_handlers(ChatOpenedHandler(print_chat_opened))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.ChatOpened` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = ChatOpened

    def __init__(
        self,
        callback: _ChatOpenedCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class PhoneNumberChangeHandler(Handler[PhoneNumberChange]):
    """
    Handler for :class:`~pywa.types.PhoneNumberChange` updates (user changes their phone number).

    - You can use the :func:`~pywa.client.WhatsApp.on_phone_number_change` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_phone_number_change = lambda _, msg: print(msg)
        >>> wa.add_handlers(PhoneNumberChangeHandler(print_phone_number_change))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.system.PhoneNumberChange` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = PhoneNumberChange

    def __init__(
        self,
        callback: _PhoneNumberChangeCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class IdentityChangeHandler(Handler[PhoneNumberChange]):
    """
    Handler for :class:`~pywa.types.system.IdentityChange` updates (user changes their identity).

    - You can use the :func:`~pywa.client.WhatsApp.on_identity_change` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_identity_change = lambda _, msg: print(msg)
        >>> wa.add_handlers(IdentityChangeHandler(print_identity_change))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.system.IdentityChange` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = IdentityChange

    def __init__(
        self,
        callback: _IdentityChangeCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class TemplateStatusUpdateHandler(Handler[TemplateStatusUpdate]):
    """
    Handler for :class:`~pywa.types.templates.TemplateStatusUpdate` updates (Template status updates, e.g. ``approved``, ``rejected`` etc.).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_status_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_template_status_update = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateStatusUpdateHandler(print_template_status_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.templates.TemplateStatusUpdate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)

    """

    _update = TemplateStatusUpdate

    def __init__(
        self,
        callback: _TemplateStatusUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class TemplateCategoryUpdateHandler(Handler[TemplateCategoryUpdate]):
    """
    Handler for :class:`~pywa.types.templates.TemplateCategoryUpdate` updates (Template category updates, e.g. from ``UTILITY`` to ``MARKETING``).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_category_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_template_category_update = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateCategoryUpdateHandler(print_template_category_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.templates.TemplateCategoryUpdate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)

    """

    _update = TemplateCategoryUpdate

    def __init__(
        self,
        callback: _TemplateCategoryUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class TemplateQualityUpdateHandler(Handler[TemplateQualityUpdate]):
    """
    Handler for :class:`~pywa.types.templates.TemplateQualityUpdate` updates (Template quality updates, e.g. ``GREEN`` to ``RED``).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_quality_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_template_quality_update = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateQualityUpdateHandler(print_template_quality_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.templates.TemplateQualityUpdate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = TemplateQualityUpdate

    def __init__(
        self,
        callback: _TemplateQualityUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class TemplateComponentsUpdateHandler(Handler[TemplateComponentsUpdate]):
    """
    Handler for :class:`~pywa.types.templates.TemplateComponentsUpdate` updates (Template components updates, e.g. when a template component is added or removed).

    - You can use the :func:`~pywa.client.WhatsApp.on_template_components_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_template_components_update = lambda _, msg: print(msg)
        >>> wa.add_handlers(TemplateComponentsUpdateHandler(print_template_components_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.templates.TemplateComponentsUpdate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = TemplateComponentsUpdate

    def __init__(
        self,
        callback: _TemplateComponentsUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class UserMarketingPreferencesHandler(Handler[UserMarketingPreferences]):
    """
    Handler for :class:`~pywa.types.user_preferences.UserMarketingPreferences` updates (User marketing preferences updates).

    - You can use the :func:`~pywa.client.WhatsApp.on_user_marketing_preferences` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_user_marketing_preferences = lambda _, msg: print(msg)
        >>> wa.add_handlers(UserMarketingPreferencesHandler(print_user_marketing_preferences))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.user_preferences.UserMarketingPreferences` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = UserMarketingPreferences

    def __init__(
        self,
        callback: _UserMarketingPreferencesCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class FlowCompletionHandler(Handler[FlowCompletion]):
    """
    Handler for :class:`~pywa.types.flows.FlowCompletion` updates (Flow completion updates).

    - You can use the :func:`~pywa.client.WhatsApp.on_flow_completion` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_flow_completion = lambda _, msg: print(msg)
        >>> wa.add_handlers(FlowCompletionHandler(print_flow_completion))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.flows.FlowCompletion` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = FlowCompletion

    def __init__(
        self,
        callback: _FlowCompletionCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class CallConnectHandler(Handler[CallConnect]):
    """
    Handler for :class:`~pywa.types.calls.CallConnect` updates (Call connect updates).

    - You can use the :func:`~pywa.client.WhatsApp.on_call_connect` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_call_connect = lambda _, msg: print(msg)
        >>> wa.add_handlers(CallConnectHandler(print_call_connect))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.calls.CallConnect` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallConnect

    def __init__(
        self,
        callback: _CallConnectCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class CallTerminateHandler(Handler[CallTerminate]):
    """
    Handler for :class:`~pywa.types.calls.CallTerminate` updates (Call terminate updates).

    - You can use the :func:`~pywa.client.WhatsApp.on_call_terminate` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_call_terminate = lambda _, msg: print(msg)
        >>> wa.add_handlers(CallTerminateHandler(print_call_terminate))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.calls.CallTerminate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallTerminate

    def __init__(
        self,
        callback: _CallTerminateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class CallStatusHandler(_FactoryHandler[CallStatus]):
    """
    Handler for :class:`~pywa.types.calls.CallStatus` updates (Call status updates, e.g. ``ringing``, ``accepted``, ``rejected``, etc.).

    - You can use the :func:`~pywa.client.WhatsApp.on_call_status` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_call_status = lambda _, msg: print(msg)
        >>> wa.add_handlers(CallStatusHandler(print_call_status))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.calls.CallStatus` as positional arguments)
        filters: The filters to apply to the handler
        factory: The :class:`~pywa.types.callback.CallbackData` constructor to use to construct the ``tracker`` data.
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallStatus
    _data_field = "tracker"

    def __init__(
        self,
        callback: _CallStatusCallback,
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


class CallPermissionUpdateHandler(Handler[CallPermissionUpdate]):
    """
    Handler for :class:`~pywa.types.calls.CallPermissionUpdate` updates (Call permission updates, e.g. when a user grants or revokes permission to receive calls).

    - You can use the :func:`~pywa.client.WhatsApp.on_call_permission_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_call_permission_update = lambda _, msg: print(msg)
        >>> wa.add_handlers(CallPermissionUpdateHandler(print_call_permission_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a :class:`~pywa.types.calls.CallPermissionUpdate` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = CallPermissionUpdate

    def __init__(
        self,
        callback: _CallPermissionUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


class RawUpdateHandler(Handler[dict]):
    """
    Handler for raw updates (dicts) from the webhook.

    - You can use the :func:`~pywa.client.WhatsApp.on_raw_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(...)
        >>> print_raw_update = lambda _, update: print(update)
        >>> wa.add_handlers(RawUpdateHandler(print_raw_update))

    Args:
        callback: The callback function (Takes a :class:`~pywa.client.WhatsApp` instance and a raw update :class:`dict` as positional arguments)
        filters: The filters to apply to the handler
        priority: The priority of the handler (default: ``0``)
    """

    _update = None

    def __init__(
        self,
        callback: _RawUpdateCallback,
        filters: Filter = None,
        priority: int = 0,
    ):
        super().__init__(callback=callback, filters=filters, priority=priority)


_flow_req_has_error_filter = new_filter(
    lambda _, r: r.has_error, name="flow request has error"
)


def _get_filters_with_error_filter(
    filters: Filter | None, handle_errors: bool
) -> Filter | None:
    error_filter = (
        _flow_req_has_error_filter if handle_errors else ~_flow_req_has_error_filter
    )
    return (error_filter & filters) if filters is not None else error_filter


class _CallbackWrapperDecorators(abc.ABC):
    @abc.abstractmethod
    def add_handler(
        self,
        *,
        callback: _FlowRequestHandlerT,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> _CallbackWrapperDecorators: ...

    @abc.abstractmethod
    def add_completion_handler(
        self,
        handler: FlowCompletionHandler,
    ) -> _CallbackWrapperDecorators: ...

    def on(
        self,
        *,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT] | _FlowRequestHandlerT:
        """
        Decorator to help you add more handlers to the same endpoint and split the logic into multiple functions.

        You can use this shortcuts: :meth:`on_init`, :meth:`on_data_exchange`, :meth:`on_back`.

        Args:
            action: The action type to listen to.
            screen: The screen to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The function itself.
        """

        def decorator(callback: _FlowRequestHandlerT) -> _FlowRequestHandlerT:
            self.add_handler(
                callback=callback, action=action, screen=screen, filters=filters
            )
            return callback

        return decorator

    def on_init(
        self=None, filters: Filter = None, *, call_on_error: bool = False
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add a handler for the :class:`FlowRequestActionType.INIT` action.

        - This request arrives when the :class:`~pywa.types.callback.FlowButton` sent with action_type of :class:`FlowRequestActionType.DATA_EXCHANGE`.

        Example:

            >>> wa = WhatsApp(...)

            >>> wa.send_text(to=..., buttons=FlowButton(
            ...     # This will trigger the `INIT` request when the user clicks the button.
            ...     flow_action_type=FlowActionType.DATA_EXCHANGE, ...
            ... ))

            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...

            >>> @feedback_flow_handler.on_init  # This will be called when the flow is started.
            >>> def on_init(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     return req.respond(...)

        Args:
            filters: A filter function to apply to the incoming request.
            call_on_error: Whether to call the handler when the request has an error (The return value of the callback will be ignored).

        Returns:
            The callback function.
        """
        if callable(filters):  # @handler.on_init
            self.add_handler(
                callback=filters,
                action=FlowRequestActionType.INIT,
                filters=_get_filters_with_error_filter(None, call_on_error),
            )
            return filters

        def deco(callback: _FlowRequestHandlerT) -> _FlowRequestHandlerT:
            self.add_handler(
                callback=callback,
                action=FlowRequestActionType.INIT,
                filters=_get_filters_with_error_filter(filters, call_on_error),
            )
            return callback

        return deco

    def on_data_exchange(
        self=None,
        screen: Screen | str | None = None,
        filters: Filter = None,
        *,
        call_on_error: bool = False,
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add a handler for the :class:`FlowRequestActionType.DATA_EXCHANGE` action.

        - This request arrives when using :class:`~pywa.types.flows.DataExchangeAction` in the flow. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.
        - This callback must return a :class:`~pywa.types.flows.FlowResponse` object, a :class:`dict` or to raise :class:`~pywa.types.flows.FlowResponseError` subclass.

        Example:

            >>> wa = WhatsApp(...)

            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...    ...

            >>> @feedback_flow_handler.on_data_exchange(screen="SURVEY", filters=filters.new(lambda _, r: r.data["rating"] == "5"))
            >>> def on_survey_with_rating_5(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     return req.respond(...)

        Args:
            screen: The screen to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.
            call_on_error: Whether to call the handler when the request has an error (The return value of the callback will be ignored).

        Returns:
            The callback function.
        """
        if callable(screen):  # @handler.on_data_exchange
            self.add_handler(
                callback=screen,
                action=FlowRequestActionType.DATA_EXCHANGE,
                screen=None,
                filters=_get_filters_with_error_filter(None, call_on_error),
            )
            return screen

        def deco(callback: _FlowRequestHandlerT) -> _FlowRequestHandlerT:
            self.add_handler(
                callback=callback,
                action=FlowRequestActionType.DATA_EXCHANGE,
                screen=screen,
                filters=_get_filters_with_error_filter(filters, call_on_error),
            )
            return callback

        return deco

    def on_back(
        self=None,
        *,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> Callable[[_FlowRequestHandlerT], _FlowRequestHandlerT]:
        """
        Decorator to add a handler for the :class:`FlowRequestActionType.BACK` action.

        - This request arrives when the user clicks the back button in the WhatsApp client and the flows screen ``refresh_on_back`` is set to ``True``.
        - This callback must return a :class:`~pywa.types.flows.FlowResponse` object, a :class:`dict` or to raise :class:`~pywa.types.flows.FlowResponseError` subclass.

        Example:

            >>> wa = WhatsApp(...)

            >>> @wa.on_flow_request("/feedback_flow")
            >>> def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...     ...

            >>> @feedback_flow_handler.on_back(screen="SURVEY")
            >>> def on_back(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     return req.respond(...)

        Args:
            screen: The screen to listen to (if screen is not provided, the handler will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The callback function.
        """
        if callable(screen):
            self.add_handler(
                callback=screen,
                action=FlowRequestActionType.BACK,
                screen=None,
                filters=filters,
            )
            return screen

        def deco(callback: _FlowRequestHandlerT) -> _FlowRequestHandlerT:
            self.add_handler(
                callback=callback,
                action=FlowRequestActionType.BACK,
                screen=screen,
                filters=filters,
            )
            return callback

        return deco

    def on_completion(
        self=None,
        filters: Filter = None,
        *,
        priority: int = 0,
    ) -> Callable[[_FlowCompletionCallback], _FlowCompletionCallback]:
        """
        Decorator to add a handler for flow completion requests.

        **The :class:`FlowCompletion` update is not sent to the flow endpoint, but to the webhook endpoint.**

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/feedback_flow")
            ... def feedback_flow_handler(_: WhatsApp, req: FlowRequest):
            ...     ...

            >>> @feedback_flow_handler.on_completion(filters=filters.new(lambda _, flow: flow.response["rating"] == "5"))
            ... def on_flow_completion(_: WhatsApp, flow: FlowCompletion):
            ...     print("Flow completed with rating 5")
        """
        if callable(filters):
            self.add_completion_handler(
                FlowCompletionHandler(callback=filters, filters=None, priority=priority)
            )
            return filters

        def deco(callback: _FlowCompletionCallback) -> _FlowCompletionCallback:
            self.add_completion_handler(
                FlowCompletionHandler(
                    callback=callback, filters=filters, priority=priority
                )
            )
            return callback

        return deco


class FlowRequestHandler(_CallbackWrapperDecorators):
    """
    A handler for Flow Data Exchange requests.

    Args:
        callback: The function to call when a request is received (Takes a :class:`pywa.WhatsApp` instance and a
         :class:`pywa.types.FlowRequest` as arguments and returns a :class:`pywa.types.FlowResponse`.
        endpoint: The endpoint to listen to (The endpoint uri you set to the flow. e.g ``/feedback_flow``).
        acknowledge_errors: Whether to acknowledge errors (The return value of the callback will be ignored, and
         pywa will acknowledge the error automatically).
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
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ):
        self._main_handler = callback
        self._handlers: dict[
            tuple[FlowRequestActionType | str, str | None],
            list[tuple[Filter | None, _FlowRequestHandlerT]],
        ] = collections.defaultdict(list)  # {(action, screen?): [(filters?, callback)]}
        self._completion_handlers: list[FlowCompletionHandler] = []
        self._endpoint = endpoint
        self._acknowledge_errors = acknowledge_errors
        self._private_key = private_key
        self._private_key_password = private_key_password
        self._request_decryptor = request_decryptor
        self._response_encryptor = response_encryptor

    def add_handler(
        self,
        *,
        callback: _FlowRequestHandlerT,
        action: FlowRequestActionType,
        screen: Screen | str | None = None,
        filters: Filter = None,
    ) -> _CallbackWrapperDecorators:
        self._handlers[(action, screen)].append((filters, callback))
        return self

    def add_completion_handler(
        self, handler: FlowCompletionHandler
    ) -> _CallbackWrapperDecorators:
        """
        Add a handler for flow completion requests.

        Args:
            handler: The handler to add.
        """
        self._completion_handlers.append(handler)
        return self


_flow_request_handler_attr = "__pywa_flow_request_handler"
"""Indicates that the function is a flow request handler that should be registered."""


class _HandlerDecorators:
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
        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.RawUpdateHandler`.

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
        Decorator to register a function as a callback for incoming :class:`~pywa.types.Message`.

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.MessageHandler`.

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
        Decorator to register a function as a callback for incoming :class:`~pywa.types.CallbackButton` (when a user clicks on a :class:`~pywa.types.callback.Button` or :class:`~pywa.types.templates.QuickReplyButton`).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallbackButtonHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_button(filters.matches("help"))
            ... def help_handler(_: WhatsApp, btn: types.CallbackButton):
            ...     btn.reply_text(text="What can I help you with?")

        Args:
            filters: Filters to apply to the incoming callback button presses.
            factory: The :class:`~pywa.types.callback.CallbackData` subclass to use to construct the callback data.
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
        Decorator to register a function as a callback for incoming :class:`~pywa.types.CallbackSelection` (when a user selects an :class:`~pywa.types.callback.SectionRow` from a :class:`~pywa.types.callback.SectionList`.).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallbackSelectionHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_callback_selection(filters.startswith("id:"))
            ... def id_handler(_: WhatsApp, sel: types.CallbackSelection):
            ...     sel.reply_text(text=f"Your ID is {sel.data.split(':', 1)[1]}")

        Args:
            filters: Filters to apply to the incoming callback selections.
            factory: The :class:`~pywa.types.callback.CallbackData` subclass to use to construct the callback data.
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
        Decorator to register a function as a callback for incoming :class:`~pywa.types.message_status.MessageStatus` (when a message status changes, e.g. ``sent``, ``delivered``, ``read``, ``failed``).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.MessageStatusHandler`.

        **DO NOT USE THIS HANDLER WITHOUT FILTERS TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_message_status(filters.failed)
            ... def delivered_handler(client: WhatsApp, status: types.MessageStatus):
            ...     print(f"Message {status.id} failed to send to {status.from_user.wa_id}: {status.error.message})


        Args:
            filters: Filters to apply to the incoming message status changes.
            factory: The :class:`~pywa.types.callback.CallbackData` subclass to use to construct the ``tracker`` data.
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
        Decorator to register a function as a callback for incoming :class:`~pywa.types.ChatOpened` (when a user opens a chat with the business).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.ChatOpenedHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_chat_opened
            ... def chat_opened_handler(client: WhatsApp, chat_opened: types.ChatOpened):
            ...     print(f"The user {chat_opened.from_user.wa_id} just opened a chat with us!")

        Args:
            filters: Filters to apply to the incoming chat opened events.
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

    def on_phone_number_change(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_PhoneNumberChangeCallback], _PhoneNumberChangeCallback]
        | _PhoneNumberChangeCallback
    ):
        """
        Decorator to register a function as a callback for incoming :class:`~pywa.types.system.PhoneNumberChange` (when a user changes their phone number).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.PhoneNumberChangeHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_phone_number_change
            ... def phone_number_change_handler(client: WhatsApp, phone_number_change: types.PhoneNumberChange):
            ...     print(f"The user {phone_number_change.from_user.wa_id} just changed their phone number to {phone_number_change.new_phone_number}!")

        Args:
            filters: Filters to apply to the incoming phone number change events.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=PhoneNumberChangeHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _PhoneNumberChangeCallback) -> _PhoneNumberChangeCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=PhoneNumberChangeHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_identity_change(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_IdentityChangeCallback], _IdentityChangeCallback]
        | _IdentityChangeCallback
    ):
        """
        Decorator to register a function as a callback for incoming :class:`~pywa.types.system.IdentityChange` (when a user changes their identity).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.IdentityChangeHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_identity_change
            ... def identity_change_handler(client: WhatsApp, identity_change: types.IdentityChange):
            ...     print(f"The user {identity_change.from_user.wa_id} just changed their identity!: {identity_change.body}")

        Args:
            filters: Filters to apply to the incoming identity change events.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=IdentityChangeHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _IdentityChangeCallback) -> _IdentityChangeCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=IdentityChangeHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_template_status_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_TemplateStatusUpdateCallback], _TemplateStatusUpdateCallback]
        | _TemplateStatusUpdateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.templates.TemplateStatusUpdate` updates (Template status changed, e.g. ``approved``, ``rejected``, etc.).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.TemplateStatusUpdateHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_status_update
            ... def approved_handler(client: WhatsApp, update: types.TemplateStatusUpdate):
            ...     print(f"Template {update.template_name} just got {update.new_status}!")

        Args:
            filters: Filters to apply to the incoming template status changes.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=TemplateStatusUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _TemplateStatusUpdateCallback,
        ) -> _TemplateStatusUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=TemplateStatusUpdateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_template_category_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_TemplateCategoryUpdateCallback], _TemplateCategoryUpdateCallback]
        | _TemplateCategoryUpdateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.templatesCategoryUpdate` updates (Template category changed, e.g. from ``UTILITY`` to ``MARKETING``).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.TemplateCategoryUpdateHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_category_update
            ... def category_update_handler(client: WhatsApp, update: types.TemplateCategoryUpdate):
            ...     print(f"Template {update.template_name} category changed from {update.previous_category} to {update.new_category}!")

        Args:
            filters: Filters to apply to the incoming template category changes.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=TemplateCategoryUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _TemplateCategoryUpdateCallback,
        ) -> _TemplateCategoryUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=TemplateCategoryUpdateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_template_quality_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_TemplateQualityUpdateCallback], _TemplateQualityUpdateCallback]
        | _TemplateQualityUpdateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.templates.TemplateQualityUpdate` updates (Template quality changed).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.TemplateQualityUpdateHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_quality_update
            ... def quality_update_handler(client: WhatsApp, update: types.TemplateQualityUpdate):
            ...     print(f"Template {update.template_name} quality changed to {update.new_quality_score}!")

        Args:
            filters: Filters to apply to the incoming template quality changes.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=TemplateQualityUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _TemplateQualityUpdateCallback,
        ) -> _TemplateQualityUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=TemplateQualityUpdateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_template_components_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_TemplateComponentsUpdateCallback], _TemplateComponentsUpdateCallback]
        | _TemplateComponentsUpdateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`pywa.types.templates.TemplateComponentsUpdate` updates (Template components changed).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.TemplateComponentsUpdateHandler`.

        Example:

            >>> from pywa import WhatsApp, types, filters
            >>> wa = WhatsApp(...)
            >>> @wa.on_template_components_update
            ... def components_update_handler(client: WhatsApp, update: types.TemplateComponentsUpdate):
            ...     print(f"Template {update.template_name} components updated!")

        Args:
            filters: Filters to apply to the incoming template components changes.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=TemplateComponentsUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _TemplateComponentsUpdateCallback,
        ) -> _TemplateComponentsUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=TemplateComponentsUpdateHandler,
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
        Decorator to register a function as a callback for :class:`~pywa.types.FlowCompletion` updates (:class:`~pywa.types.callback.FlowButton` is completed).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.FlowCompletionHandler`.

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

    def on_call_connect(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> Callable[[_CallConnectCallback], _CallConnectCallback] | _CallConnectCallback:
        """
        Decorator to register a function as a callback for :class:`~pywa.types.calls.CallConnect` updates (incoming/outgoing call).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallConnectHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_call_connect
            ... def incoming_call_handler(client: WhatsApp, call: types.CallConnect):
            ...     print(f"You getting an incoming call from {call.from_user.name}")
            ...     call.accept()


        Args:
            filters: Filters to apply to the incoming call connect.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallConnectHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _CallConnectCallback) -> _CallConnectCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallConnectHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_call_terminate(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_CallTerminateCallback], _CallTerminateCallback]
        | _CallTerminateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.calls.CallTerminate` updates (when a call is ended).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallTerminateHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_call_terminate
            ... def on_hangup(client: WhatsApp, call: types.CallTerminate):
            ...     print(f"The call {call.from_user.name} is terminated")

        Args:
            filters: Filters to apply to the incoming call terminate.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallTerminateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(callback: _CallTerminateCallback) -> _CallTerminateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallTerminateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_call_status(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        factory: type[CallbackData] | None = None,
        priority: int = 0,
    ) -> Callable[[_CallStatusCallback], _CallStatusCallback] | _CallStatusCallback:
        """
        Decorator to register a function as a callback for :class:`~pywa.types.calls.CallStatus` updates (when a call status changes, e.g. ``ringing``, ``accepted``, ``rejected``, etc.).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallStatusHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_call_status
            ... def on_status(client: WhatsApp, call: types.CallStatus):
            ...     print(f"The call with {call.from_user.name} is {call.status}")

        Args:
            filters: Filters to apply to the incoming call status.
            factory: The constructor to use to construct the callback data.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallStatusHandler,
                filters=filters,
                priority=priority,
                factory=factory,
            )
        ) is not None:
            return clb

        def deco(callback: _CallStatusCallback) -> _CallStatusCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallStatusHandler,
                callback=callback,
                filters=filters,
                priority=priority,
                factory=factory,
            )

        return deco

    def on_call_permission_update(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_CallPermissionUpdateCallback], _CallPermissionUpdateCallback]
        | _CallPermissionUpdateCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.calls.CallPermissionUpdate` updates (when the user accepts or rejects the :class:`~pywa.types.callback.CallPermissionRequestButton`).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.CallPermissionUpdateHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_call_permission_update
            ... def call_permission_handler(client: WhatsApp, update: types.CallPermissionUpdate):
            ...     if update: # Use boolean context to check if the call permission is granted
            ...         update.reply("We will now be able to call you!")
            ...         update.call(...)

        Args:
            filters: Filters to apply to the incoming call permission updates.
            priority: The priority of the handler (default: ``0``).
        """
        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=CallPermissionUpdateHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _CallPermissionUpdateCallback,
        ) -> _CallPermissionUpdateCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=CallPermissionUpdateHandler,
                callback=callback,
                filters=filters,
                priority=priority,
            )

        return deco

    def on_user_marketing_preferences(
        self: WhatsApp | Filter = None,
        filters: Filter = None,
        priority: int = 0,
    ) -> (
        Callable[[_UserMarketingPreferencesCallback], _UserMarketingPreferencesCallback]
        | _UserMarketingPreferencesCallback
    ):
        """
        Decorator to register a function as a callback for :class:`~pywa.types.user_preferences.UserMarketingPreferences` updates (User wants to stop or resume receiving marketing :class:`~pywa.types.templates.Template` 's).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.UserMarketingPreferencesHandler`.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_user_marketing_preferences
            ... def user_marketing_preferences_handler(client: WhatsApp, prefs: types.UserMarketingPreferences):
            ...     if not prefs: # use boolean context to check if the user wants to stop receiving marketing messages
            ...         print(f"The user {prefs.from_user.wa_id} wants to stop receiving marketing messages.")

        Args:
            filters: Filters to apply to the incoming user marketing preferences updates.
            priority: The priority of the handler (default: ``0``).
        """

        if (
            clb := _registered_without_parentheses(
                self=self,
                handler_type=UserMarketingPreferencesHandler,
                filters=filters,
                priority=priority,
            )
        ) is not None:
            return clb

        def deco(
            callback: _UserMarketingPreferencesCallback,
        ) -> _UserMarketingPreferencesCallback:
            return _registered_with_parentheses(
                self=self,
                handler_type=UserMarketingPreferencesHandler,
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
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ) -> Callable[
        [_FlowRequestHandlerT],
        FlowRequestCallbackWrapper | FlowRequestHandler,
    ]:
        """
        Decorator to register a function to handle and respond to incoming :class:`~pywa.types.flows.FlowRequest` (when a user interacts with a flow. e.g. trigger :class:`~pywa.types.flows.DataExchangeAction` or navigates to a screen in a flow).

        - Shortcut for :func:`~pywa.client.WhatsApp.add_handlers` with a :class:`~pywa.handlers.FlowRequestHandler`.

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
                handler = FlowRequestHandler(
                    callback=callback,
                    endpoint=ep,
                    acknowledge_errors=acknowledge_errors,
                    private_key=private_key,
                    private_key_password=private_key_password,
                    request_decryptor=request_decryptor,
                    response_encryptor=response_encryptor,
                )
                setattr(handler, _flow_request_handler_attr, None)
                return handler

            callback_wrapper = self._register_flow_endpoint_callback(
                endpoint=endpoint,
                callback=callback,
                acknowledge_errors=acknowledge_errors,
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


class FlowRequestCallbackWrapper(_CallbackWrapperDecorators):
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
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ):
        wa._check_for_async_callback(callback)
        self._wa = wa
        self._endpoint = endpoint
        self._main_handler = callback
        self._handlers: dict[
            tuple[FlowRequestActionType | str, str | None],
            list[tuple[Filter | None, _FlowRequestHandlerT]],
        ] = collections.defaultdict(list)  # {(action, screen?): [(filters?, callback)]}
        self._acknowledge_errors = acknowledge_errors
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
        ) and not utils.is_cryptography_installed:
            raise ValueError(
                "The default decryptor/encryptor requires the `cryptography` package to be installed."
                '\n>> Install it with `pip install cryptography` / pip install "pywa[cryptography]" or use a '
                "custom decryptor/encryptor."
            )

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

        Args:
            callback: The callback function to handle this particular request.
            action: The action type to listen to.
            screen: The screen to listen to (if screen is not provided, the callback will be called for all screens for this action!).
            filters: A filter function to apply to the incoming request.

        Returns:
            The current instance.
        """
        self._wa._check_for_async_callback(callback)
        self._wa._check_for_async_filters(filters)
        self._handlers[
            (action, screen.id if isinstance(screen, Screen) else screen)
        ].append((filters, callback))
        return self

    def add_completion_handler(
        self, handler: FlowCompletionHandler
    ) -> FlowRequestCallbackWrapper:
        """
        Add a handler for flow completion events.

        - This is a shortcut for adding a handler for the `FlowCompletionHandler` type.

        Args:
            handler: The FlowCompletionHandler instance to add.

        Returns:
            The current instance.
        """
        self._wa.add_handlers(handler)
        return self

    def _get_callback(self, req: FlowRequest) -> _FlowRequestHandlerT:
        """Resolve the callback to use for the incoming request."""
        for filters, callback in (
            *self._handlers[(req.action, None)],  # Precedence to no-screen handlers
            *self._handlers[(req.action, req.screen)],
        ):
            if filters is None or filters.check_sync(self._wa, req):
                return callback
        return self._main_handler

    async def _get_callback_async(self, req: FlowRequest) -> _FlowRequestHandlerT:
        """Resolve the callback to use for the incoming request (async version)."""
        for filters, callback in (
            *self._handlers[(req.action, None)],  # Precedence to no-screen handlers
            *self._handlers[(req.action, req.screen)],
        ):
            if filters is None or await filters.check_async(self._wa, req):
                return callback
        return self._main_handler

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

        if decrypted_request["action"] == "ping":
            _logger.debug(
                "Flow Endpoint ('%s'): Received a health check request",
                self._endpoint,
            )
            return self._encrypt_response(
                {
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
            return "pywa: Failed to construct FlowRequest object", 500

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

        if decrypted_request["action"] == "ping":
            return self._encrypt_response(
                {
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
            return "pywa: Failed to construct FlowRequest object", 500

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
            if isinstance(
                res, FlowResponseError
            ):  # typing backward compatibility. error should be raised, not returned
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
        if not isinstance(res, (FlowResponse, dict)):
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
            if isinstance(
                res, FlowResponseError
            ):  # typing backward compatibility. error should be raised, not returned
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
        if not isinstance(res, (FlowResponse, dict)):
            raise TypeError(
                f"Flow endpoint ('{self._endpoint}') callback ('{callback.__name__}') must return a `FlowResponse`"
                f" or `dict`, not {type(res)}"
            )
        return self._encrypt_response(
            res.to_dict() if isinstance(res, FlowResponse) else res,
            aes_key,
            iv,
        ), 200
