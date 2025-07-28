from __future__ import annotations

from pywa.listeners import *  # noqa MUST BE IMPORTED FIRST
from pywa.listeners import (
    Listener as _Listener,
    BaseListenerIdentifier,
)  # noqa MUST BE IMPORTED FIRST

import asyncio
from typing import TYPE_CHECKING, TypeAlias

from pywa import utils, _helpers as helpers
from pywa.types.base_update import BaseUpdate
from .filters import Filter
from .types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    ChatOpened,
    FlowCompletion,
)

if TYPE_CHECKING:
    from .client import WhatsApp


class Listener(_Listener):
    _listener_canceled = ListenerCanceled

    def __init__(
        self,
        wa: WhatsApp,
        identifier: BaseListenerIdentifier,
        filters: Filter,
        cancelers: Filter,
    ):
        self.filters = filters
        self.cancelers = cancelers
        self.future: asyncio.Future[BaseUpdate] = asyncio.Future()
        self.future.add_done_callback(
            lambda _: wa._remove_listener(identifier=identifier)
        )

    def set_result(self, result: BaseUpdate) -> None:
        self.future.set_result(result)

    def set_exception(self, exception: Exception) -> None:
        self.future.set_exception(exception)

    def is_set(self) -> bool:
        return self.future.done()

    async def apply_filters(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return not self.filters or await self.filters.check_async(wa, update)

    async def apply_cancelers(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return self.cancelers and await self.cancelers.check_async(wa, update)


class _AsyncListeners:
    async def listen(
        self: WhatsApp,
        to: BaseListenerIdentifier,
        *,
        filters: Filter = None,
        cancelers: Filter = None,
        timeout: float | None = None,
    ) -> BaseUpdate:
        """
        Listen to an update.

        - You can use one of the shortcuts to listen to a specific update type:
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_reply`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_click`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_selection`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_completion`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_until_read`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_until_delivered`

        Example:

            .. code-block:: python

                    try:
                        await wa.send_message(
                            to="123456",
                            text="Send me a message",
                            buttons=[Button(title="Cancel", callback_data="cancel")]
                        )
                        update: Message = wa.listen(
                            to=UserUpdateListenerIdentifier(sender="123456", recipient="654321"),
                            filters=filters.message & filters.text,
                            cancelers=filters.callback_button & filters.matches("cancel"),
                            timeout=10
                        )
                        print(update)
                    except ListenerTimeout:
                        print("Listener timed out")
                    except ListenerCanceled:
                        print("Listener was canceled")
                    except ListenerStopped:
                        print("Listener was stopped")

        Args:
            to: The identifier of the update to listen to.
            filters: The filters to apply to the update, return the update if the filters pass.
            cancelers: The filters to cancel the listening, raise :class:`ListenerCanceled` if the update matches.
            timeout: The time to wait for the update, raise :class:`ListenerTimeout` if the time passes

        Returns:
            The update that passed the filters

        Raises:
            ListenerTimeout: If the listener timed out
            ListenerCanceled: If the listener was canceled by a filter
            ListenerStopped: If the listener was stopped manually
        """
        if self._server is utils.MISSING:
            raise ValueError(
                "You must initialize the WhatsApp client with an web app"
                " (Flask or FastAPI or custom server by setting `server` to None) in order to listen to incoming updates."
            )
        listener = Listener(
            wa=self,
            identifier=to,
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[to] = listener
        try:
            return await asyncio.wait_for(listener.future, timeout=timeout)
        except asyncio.TimeoutError:
            raise ListenerTimeout(timeout)
