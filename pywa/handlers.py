"""
This module contains the handlers for incoming updates.
"""

from __future__ import annotations

__all__ = [
    "MessageHandler",
    "CallbackButtonHandler",
    "CallbackSelectionHandler",
    "RawUpdateHandler",
    "MessageStatusHandler"
]

from typing import Callable, Any, TYPE_CHECKING
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class Handler:
    """Base class for all handlers."""
    __handler_type__ = None

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


class MessageHandler(Handler):
    """
    Handler for incoming messages (text, image, video, etc.).
        - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a handler for this type.

    Args:
        handler: The handler function. (gets the WhatsApp instance and the message as arguments)
        filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the message as arguments and returns a boolean)
    """
    __handler_type__ = "message"

    def __init__(
            self,
            handler: Callable[[WhatsApp, Message], Any],
            *filters: Callable[[WhatsApp, Message], bool]
    ):
        super().__init__(handler, *filters)


class CallbackButtonHandler(Handler):
    """
    A button callback handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Args:
        handler: The handler function. (gets the WhatsApp instance and the callback as arguments)
        filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the callback as arguments and returns a boolean)
    """
    __handler_type__ = "button"

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackButton], Any],
            *filters: Callable[[WhatsApp, CallbackButton], bool]
    ):
        super().__init__(handler, *filters)


class CallbackSelectionHandler(Handler):
    """
    A selection callback handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Args:
        handler: The handler function. (gets the WhatsApp instance and the callback as arguments)
        filters: The filters to apply to the handler. (gets the WhatsApp instance and
    """
    __handler_type__ = "selection"

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackSelection], Any],
            *filters: Callable[[WhatsApp, CallbackSelection], bool]
    ):
        super().__init__(handler, *filters)


class MessageStatusHandler(Handler):
    """
    A message status handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_message_status` decorator to register a handler for this type.

    Args:
        handler: The handler function. (gets the WhatsApp instance and the message status as arguments)
        filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the message status as arguments and returns a boolean)
    """
    __handler_type__ = "message_status"

    def __init__(
            self,
            handler: Callable[[WhatsApp, MessageStatus], Any],
            *filters: Callable[[WhatsApp, MessageStatus], bool]
    ):
        super().__init__(handler, *filters)


class RawUpdateHandler(Handler):
    """
    A raw update handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_raw_update` decorator to register a handler for this type.

    Args:
        handler: The handler function. (gets the WhatsApp instance and the data-dict as arguments)
        filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the data-dict as arguments and returns a boolean)
    """
    __handler_type__ = "raw_update"

    def __init__(
            self,
            handler: Callable[[WhatsApp, dict], Any],
            *filters: Callable[[WhatsApp, dict], bool]
    ):
        super().__init__(handler, *filters)
