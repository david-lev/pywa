from typing import Callable, Any, TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from pywa import WhatsApp


class Handler:
    """Base class for all handlers."""
    __handler_type__ = None

    def __init__(
            self,
            handler: Callable[["WhatsApp", Any], Any],
            filters: Iterable[Callable[["WhatsApp", Any], bool]] | Callable[["WhatsApp", Any], bool] | None = None
    ):
        """
        Initialize a new handler.

        Args:
            handler: The handler function. (gets the WhatsApp instance and the data as
                arguments)
            filters: A list of filters to apply to the handler. (filter functions get the WhatsApp instance and the
                data as arguments and return a boolean value)
        """
        self.handler = handler
        self.filters = filters if isinstance(filters, Iterable) else (filters,) if filters else None

    def __call__(self, wa: "WhatsApp", data: Any):
        if all([f(wa, data) for f in self.filters]) if self.filters else True:
            self.handler(wa, data)


class MessageHandler(Handler):
    __handler_type__ = "message"
    """A message handler (e.g. text, image, video, audio, etc.)."""


class ButtonCallbackHandler(Handler):
    __handler_type__ = "button"
    """A button handler."""


class SelectionCallbackHandler(Handler):
    __handler_type__ = "selection"
    """A section handler."""


class RawUpdateHandler(Handler):
    __handler_type__ = "raw_update"
    """A raw update handler."""


class MessageStatusHandler(Handler):
    __handler_type__ = "message_status"
    """A message status handler (e.g. delivered, read, etc.)."""