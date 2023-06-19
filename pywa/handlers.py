from typing import Callable, Any, TYPE_CHECKING, Iterable
from pywa.types import Message, CallbackButton, CallbackSelection
if TYPE_CHECKING:
    from pywa import WhatsApp


class Handler:
    __handler_type__ = None

    def __init__(
            self,
            handler: Callable[["WhatsApp", Any], Any],
            filters: Iterable[Callable[["WhatsApp", Any], bool]] | Callable[["WhatsApp", Any], bool] = None
    ):
        self.handler = handler
        self.filters = filters

    def __call__(self, wa: "WhatsApp", data: Any):
        if all([f(wa, data) for f in self.filters]) if isinstance(self.filters, Iterable) else self.filters(wa, data) \
                if self.filters else True:
            self.handler(wa, data)


class MessageHandler(Handler):
    __handler_type__ = Message
    """A message handler (e.g. text, image, video, audio, etc.)."""


# class CommandHandler(Handler):
#     """A command handler (e.g. /start)."""
#
#     def __init__(
#             self,
#             handler: Callable[["WhatsApp", Any], Any],
#             commands: str | Iterable[str],
#             filters: Iterable[Callable[["WhatsApp", Any], bool]]
#     ):
#         if isinstance(commands, str):
#             filters = ((lambda msg: msg.text == commands), *(filters if filters else ()))
#         elif isinstance(commands, Iterable):
#             filters = (((lambda msg: msg.text == command.removeprefix("/")) for command in commands),
#                        *(filters if filters else ()))
#         super().__init__(handler=handler, filters=filters)


class ButtonCallbackHandler(Handler):
    __handler_type__ = CallbackButton
    """A button handler."""


class SelectionCallbackHandler(Handler):
    __handler_type__ = CallbackSelection
    """A section handler."""
