from __future__ import annotations

__all__ = [
    "ListenerTimeout",
    "ListenerCanceled",
]

import asyncio
import threading
from collections.abc import Iterable
from typing import TypeVar, Callable, TYPE_CHECKING, TypeAlias, Awaitable

from .types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    ChatOpened,
    FlowCompletion,
)
from pywa import utils
from .types.base_update import BaseUserUpdate

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


class ListenerTimeout(Exception):
    def __init__(self, timeout: int):
        self.timeout = timeout


class ListenerCanceled(Exception):
    def __init__(self, update: BaseUserUpdate | None = None):
        self.update = update


class Listener:
    def __init__(
        self,
        typ: type[_UserUpdateT],
        filters: _FiltersT,
        cancelers: _CancelersT,
    ):
        self.type = typ
        self.filters = filters or ()
        self.cancelers = cancelers or ()
        self.event = threading.Event()
        self.result: _UserUpdateT | None = None
        self.cancelled_update: BaseUserUpdate | None = None
        self.exception = None

    def set_result(self, result: _UserUpdateT) -> None:
        self.result = result
        self.event.set()

    def set_exception(self, exception: Exception) -> None:
        self.exception = exception
        self.event.set()

    def cancel(self, update: BaseUserUpdate | None = None) -> None:
        self.cancelled_update = update
        self.event.set()

    def is_set(self) -> bool:
        return self.event.is_set()

    async def apply_filters(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        for f in self.filters:
            if not (
                await f(wa, update) if asyncio.iscoroutinefunction(f) else f(wa, update)
            ):
                return False
        return True

    async def apply_cancelers(
        self, wa: WhatsApp, update: _SuppoertedUserUpdate
    ) -> bool:
        for c in self.cancelers:
            if await c(wa, update) if asyncio.iscoroutinefunction(c) else c(wa, update):
                return True
        return False


class Listeners:
    def listen(
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
        from .client import _resolve_phone_id_param

        recipient = _resolve_phone_id_param(self, to_phone_id, "to_phone_id")
        listener = Listener(
            typ=to,
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[
            utils.listener_identifier(sender=from_user, recipient=recipient)
        ] = listener
        try:
            if not listener.event.wait(timeout):
                raise ListenerTimeout(timeout)
            if listener.cancelled_update:
                raise ListenerCanceled(listener.cancelled_update)
            if listener.exception:
                raise listener.exception
            return listener.result
        finally:
            self.remove_listener(from_user, recipient)

    def remove_listener(
        self: WhatsApp, from_user: str | int, to_phone_id: str | int | None = None
    ) -> None:
        """
        Remove and cancel a listener

        Args:
            from_user: The user that the listener is listening for
            to_phone_id: The phone id that the listener is listening for

        Raises:
            ValueError: If the listener does not exist
        """
        from .client import _resolve_phone_id_param

        recipient = _resolve_phone_id_param(self, to_phone_id, "to_phone_id")
        listener_identifier = utils.listener_identifier(
            sender=from_user, recipient=recipient
        )
        try:
            listener = self._listeners[listener_identifier]
        except KeyError:
            raise ValueError("Listener does not exist")
        if not listener.is_set():
            listener.cancel()
        del self._listeners[listener_identifier]
