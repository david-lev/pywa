from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import TypeVar, Callable, TYPE_CHECKING, Coroutine, TypeAlias, Awaitable

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


class ListenerTimeout(Exception):
    pass


class ListenerCanceled(Exception):
    def __init__(self, update: BaseUserUpdateAsync):
        self.update = update


class Listener:
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
        self.filters = filters
        self.cancelers = cancelers
        self.future: asyncio.Future[_UserUpdateT] = asyncio.Future()
        self.future.add_done_callback(
            lambda _: wa.remove_listener(from_user, to_phone_id)
        )


class AsyncListeners:
    async def listen(
        self: WhatsApp,
        to: type[_UserUpdateT],
        from_user: str | int,
        filters: _FiltersT = None,
        cancelers: _CancelersT = None,
        timeout: int | None = None,
        to_phone_id: str | int | None = None,
    ) -> _UserUpdateT | None:
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
            raise ListenerTimeout
        except asyncio.CancelledError as e:
            raise ListenerCanceled(e.args[0])

    async def _answer_listener(self: WhatsApp, update: BaseUserUpdateAsync) -> bool:
        """
        Answer a listener with an update

        Args:
            update (BaseUpdate): The update to answer the listener with

        Returns:
            bool: True if the listener was answered or canceled, False otherwise
        """
        if not isinstance(update, BaseUserUpdateAsync):
            return False
        listener = self._listeners.get(update.listener_identifier)
        if listener is None:
            return False
        try:
            if isinstance(update, listener.type):
                for f in listener.filters or ():
                    if not (
                        await f(self, update)
                        if asyncio.iscoroutinefunction(f)
                        else f(self, update)
                    ):
                        break
                else:
                    listener.future.set_result(update)
                    return True

            if listener.cancelers:
                for c in listener.cancelers:
                    if (
                        await c(self, update)
                        if asyncio.iscoroutinefunction(c)
                        else c(self, update)
                    ):
                        listener.future.cancel(update)
                        return True

        except Exception as e:
            listener.future.set_exception(e)
            return True

        return True

    def remove_listener(
        self: WhatsApp, from_user: str | int, to_phone_id: str | int | None = None
    ) -> None:
        """
        Remove a listener
        """
        recipient = _resolve_phone_id_param(self, to_phone_id, "to_phone_id")
        listener_identifier = utils.listener_identifier(
            sender=from_user, recipient=recipient
        )
        listener = self._listeners.get(listener_identifier)
        listener.future.cancel()
        del self._listeners[listener_identifier]
