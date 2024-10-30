from __future__ import annotations

from pywa.listeners import *  # noqa MUST BE IMPORTED FIRST
from pywa.listeners import Listener as _Listener, ListenerCanceled as _ListenerCanceled  # noqa MUST BE IMPORTED FIRST

import asyncio
from typing import TYPE_CHECKING, TypeAlias

from pywa import utils, _helpers as helpers
from .filters import Filter
from .types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    ChatOpened,
    FlowCompletion,
)
from .types.base_update import BaseUserUpdateAsync

if TYPE_CHECKING:
    from .client import WhatsApp

_SuppoertedUserUpdate: TypeAlias = (
    Message
    | CallbackButton
    | CallbackSelection
    | MessageStatus
    | ChatOpened
    | FlowCompletion
)


class ListenerCanceled(_ListenerCanceled):
    def __init__(self, update: BaseUserUpdateAsync | None = None):
        self.update = update


class Listener(_Listener):
    _listener_canceled = ListenerCanceled

    def __init__(
        self,
        wa: WhatsApp,
        to: str | int,
        sent_to_phone_id: str | int,
        filters: Filter,
        cancelers: Filter,
    ):
        self.filters = filters
        self.cancelers = cancelers
        self.future: asyncio.Future[_SuppoertedUserUpdate] = asyncio.Future()
        self.future.add_done_callback(
            lambda _: wa._remove_listener(from_user=to, phone_id=sent_to_phone_id)
        )

    def set_result(self, result: _SuppoertedUserUpdate) -> None:
        self.future.set_result(result)

    def set_exception(self, exception: Exception) -> None:
        self.future.set_exception(exception)

    def is_set(self) -> bool:
        return self.future.done()

    async def apply_filters(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        return self.filters is None or await self.filters.check_async(wa, update)

    async def apply_cancelers(
        self, wa: WhatsApp, update: _SuppoertedUserUpdate
    ) -> bool:
        return self.cancelers and await self.cancelers.check_async(wa, update)


class AsyncListeners:
    async def listen(
        self: WhatsApp,
        to: str | int,
        filters: Filter = None,
        cancelers: Filter = None,
        timeout: int | None = None,
        sent_to_phone_id: str | int | None = None,
    ) -> _SuppoertedUserUpdate:
        """
        Listen to a user update

        - You can use one of the shortcuts to listen to a specific update type:
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_reply`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_click`
            - :meth:`~pywa_async.types.sent_message.SentMessage.wait_for_selection`
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
                            to="123456",
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
            to: The user to listen to
            filters: The filters to apply to the update, return the update if the filters pass
            cancelers: The filters to cancel the listening, raise ListenerCanceled if the update matches
            timeout: The time to wait for the update, raise ListenerTimeout if the time passes
            sent_to_phone_id: The phone id to listen for

        Returns:
            The update that passed the filters

        Raises:
            ListenerTimeout: If the listener timed out
            ListenerCanceled: If the listener was canceled by a filter
            ListenerStopped: If the listener was stopped manually
        """
        recipient = helpers.resolve_phone_id_param(
            self, sent_to_phone_id, "sent_to_phone_id"
        )
        listener = Listener(
            wa=self,
            to=to,
            sent_to_phone_id=recipient,
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[utils.listener_identifier(sender=to, recipient=recipient)] = (
            listener
        )
        try:
            return await asyncio.wait_for(listener.future, timeout=timeout)
        except asyncio.TimeoutError:
            raise ListenerTimeout(timeout)
