"""
This module contains the handlers for incoming updates.
"""

__all__ = (
    "MessageHandler",
    "ButtonCallbackHandler",
    "SelectionCallbackHandler",
    "RawUpdateHandler",
    "MessageStatusHandler"
)

from typing import Callable, Any, TYPE_CHECKING
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus

if TYPE_CHECKING:
    from pywa import WhatsApp


class Handler:
    """Base class for all handlers."""
    __handler_type__ = None

    def __init__(
            self,
            handler: Callable[["WhatsApp", Any], Any],
            *filters: Callable[["WhatsApp", Any], bool]
    ):
        """
        Initialize a new handler.
        """
        self.handler = handler
        self.filters = filters

    def __call__(self, wa: "WhatsApp", data: Any):
        if all([f(wa, data) for f in self.filters]):
            self.handler(wa, data)


class MessageHandler(Handler):
    """
    Handler for incoming messages (text, image, video, etc.).

    Args:
        handler: The handler function. (gets the "WhatsApp" instance and the message as arguments)
        filters: The filters to apply to the handler. (gets the "WhatsApp" instance and
            the message as arguments and returns a boolean)
    """
    __handler_type__ = "message"

    def __init__(
            self,
            handler: Callable[["WhatsApp", Message], Any],
            *filters: Callable[["WhatsApp", Message], bool]
    ):
        super().__init__(handler, *filters)


class ButtonCallbackHandler(Handler):
    """
    A button callback handler.

    Args:
        handler: The handler function. (gets the "WhatsApp" instance and the callback as arguments)
        filters: The filters to apply to the handler. (gets the "WhatsApp" instance and
            the callback as arguments and returns a boolean)
    """
    __handler_type__ = "button"

    def __init__(
            self,
            handler: Callable[["WhatsApp", CallbackButton], Any],
            *filters: Callable[["WhatsApp", CallbackButton], bool]
    ):
        super().__init__(handler, *filters)


class SelectionCallbackHandler(Handler):
    """
    A selection callback handler.

    Args:
        handler: The handler function. (gets the "WhatsApp" instance and the callback as arguments)
        filters: The filters to apply to the handler. (gets the "WhatsApp" instance and
    """
    __handler_type__ = "selection"

    def __init__(
            self,
            handler: Callable[["WhatsApp", CallbackSelection], Any],
            *filters: Callable[["WhatsApp", CallbackSelection], bool]
    ):
        super().__init__(handler, *filters)


class MessageStatusHandler(Handler):
    """
    A message status handler.

    Args:
        handler: The handler function. (gets the "WhatsApp" instance and the message status as arguments)
        filters: The filters to apply to the handler. (gets the "WhatsApp" instance and
            the message status as arguments and returns a boolean)
    """
    __handler_type__ = "message_status"

    def __init__(
            self,
            handler: Callable[["WhatsApp", MessageStatus], Any],
            *filters: Callable[["WhatsApp", MessageStatus], bool]
    ):
        super().__init__(handler, *filters)


class RawUpdateHandler(Handler):
    """
    A raw update handler.

    Args:
        handler: The handler function. (gets the "WhatsApp" instance and the data-dict as arguments)
        filters: The filters to apply to the handler. (gets the "WhatsApp" instance and
            the data-dict as arguments and returns a boolean)
    """
    __handler_type__ = "raw_update"

    def __init__(
            self,
            handler: Callable[["WhatsApp", dict], Any],
            *filters: Callable[["WhatsApp", dict], bool]
    ):
        super().__init__(handler, *filters)
