from __future__ import annotations


from pywa.listeners import (
    ListenerTimeout,
    ListenerCanceled as _ListenerCanceled,
    Listener as _Listener,
)

import asyncio
from collections.abc import Iterable
from typing import Callable, TYPE_CHECKING, TypeAlias, Awaitable

from pywa.types.base_update import BaseUserUpdate
from .types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    ChatOpened,
    FlowCompletion,
)
from pywa import utils
from pywa.client import _resolve_phone_id_param
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


_CancelersT: TypeAlias = (
    Iterable[
        Callable[
            [
                "WhatsApp",
                _SuppoertedUserUpdate,
            ],
            bool | Awaitable[bool],
        ]
    ]
    | None
)
_FiltersT: TypeAlias = (
    Iterable[Callable[["WhatsApp", BaseUserUpdate], bool | Awaitable[bool]]] | None
)


class ListenerCanceled(_ListenerCanceled):
    def __init__(self, update: BaseUserUpdateAsync | None = None):
        self.update = update


class Listener(_Listener):
    def __init__(
        self,
        wa: WhatsApp,
        to: str | int,
        sent_to_phone_id: str | int,
        filters: _FiltersT,
        cancelers: _CancelersT,
    ):
        self.filters = filters or ()
        self.cancelers = cancelers or ()
        self.future: asyncio.Future[_SuppoertedUserUpdate] = asyncio.Future()
        self.future.add_done_callback(
            lambda _: wa.remove_listener(from_user=to, phone_id=sent_to_phone_id)
        )

    def set_result(self, result: _SuppoertedUserUpdate) -> None:
        self.future.set_result(result)

    def set_exception(self, exception: Exception) -> None:
        self.future.set_exception(exception)

    def cancel(self, update: BaseUserUpdate | None = None) -> None:
        self.cancelled_update = update
        self.future.cancel()

    def is_set(self) -> bool:
        return self.future.done()


class AsyncListeners:
    async def listen(
        self: WhatsApp,
        to: str | int,
        filters: _FiltersT = None,
        cancelers: _CancelersT = None,
        timeout: int | None = None,
        sent_to_phone_id: str | int | None = None,
    ) -> _SuppoertedUserUpdate:
        """
        Asynchronously listen for a specific type of update from a specific user
        """
        recipient = _resolve_phone_id_param(self, sent_to_phone_id, "sent_to_phone_id")
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
        except asyncio.CancelledError:
            raise ListenerCanceled(listener.cancelled_update)
