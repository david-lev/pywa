from __future__ import annotations


from pywa.listeners import (
    ListenerTimeout,
    ListenerCanceled as _ListenerCanceled,
    Listener as _Listener,
)

import asyncio
from collections.abc import Iterable
from typing import TypeVar, Callable, TYPE_CHECKING, Coroutine, TypeAlias, Awaitable

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

_UserUpdateT = TypeVar(
    "_UserUpdateT",
    bound=_SuppoertedUserUpdate,
)
_UserUpdateCancelT = TypeVar(
    "_UserUpdateCancelT",
    bound=_SuppoertedUserUpdate,
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
    Iterable[Callable[["WhatsApp", _UserUpdateT], bool | Awaitable[bool]]] | None
)


class ListenerCanceled(_ListenerCanceled):
    def __init__(self, update: BaseUserUpdateAsync | None = None):
        self.update = update


class Listener(_Listener):
    def __init__(
        self,
        wa: WhatsApp,
        from_user: str | int,
        to_phone_id: str | int,
        typ: type[_UserUpdateT],
        filters: _FiltersT,
        cancelers: _CancelersT,
    ):
        self.type = typ
        self.filters = filters or ()
        self.cancelers = cancelers or ()
        self.future: asyncio.Future[_UserUpdateT] = asyncio.Future()
        self.future.add_done_callback(
            lambda _: wa.remove_listener(from_user, to_phone_id)
        )

    def set_result(self, result: _UserUpdateT) -> None:
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
        to: type[_UserUpdateT],
        from_user: str | int,
        filters: _FiltersT = None,
        cancelers: _CancelersT = None,
        timeout: int | None = None,
        to_phone_id: str | int | None = None,
    ) -> _UserUpdateT:
        """
        Asynchronously listen for a specific type of update from a specific user
        """
        recipient = _resolve_phone_id_param(self, to_phone_id, "to_phone_id")
        listener = Listener(
            wa=self,
            from_user=from_user,
            to_phone_id=recipient,
            typ=to,
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[
            utils.listener_identifier(sender=from_user, recipient=recipient)
        ] = listener
        try:
            result = await asyncio.wait_for(listener.future, timeout)
            return result
        except asyncio.TimeoutError:
            raise ListenerTimeout(timeout)
        except asyncio.CancelledError:
            raise ListenerCanceled(listener.cancelled_update)
