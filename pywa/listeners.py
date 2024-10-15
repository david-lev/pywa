from __future__ import annotations

__all__ = [
    "ListenerTimeout",
    "ListenerCanceled",
]

import threading
from typing import TYPE_CHECKING, TypeAlias

from pywa import utils, _helpers as helpers
from .types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    ChatOpened,
    FlowCompletion,
)
from .filters import Filter
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


class ListenerTimeout(Exception):
    def __init__(self, timeout: int):
        self.timeout = timeout


class ListenerCanceled(Exception):
    def __init__(self, update: BaseUserUpdate | None = None):
        self.update = update


class Listener:
    def __init__(
        self,
        filters: Filter | None,
        cancelers: Filter | None,
    ):
        self.filters = filters
        self.cancelers = cancelers
        self.event = threading.Event()
        self.result: _SuppoertedUserUpdate | None = None
        self.cancelled_update: BaseUserUpdate | None = None
        self.exception = None

    def set_result(self, result: BaseUserUpdate) -> None:
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

    def apply_filters(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        return self.filters is None or self.filters(wa, update)

    def apply_cancelers(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        return self.cancelers is None or self.cancelers(wa, update)


class Listeners:
    def listen(
        self: WhatsApp,
        to: str | int,
        filters: Filter | None = None,
        cancelers: Filter | None = None,
        timeout: int | None = None,
        sent_to_phone_id: str | int | None = None,
    ) -> _SuppoertedUserUpdate:
        recipient = helpers.resolve_phone_id_param(
            self, sent_to_phone_id, "sent_to_phone_id"
        )
        listener = Listener(
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[utils.listener_identifier(sender=to, recipient=recipient)] = (
            listener
        )
        try:
            if not listener.event.wait(timeout):
                raise ListenerTimeout(timeout)
            if listener.cancelled_update:
                raise ListenerCanceled(listener.cancelled_update)
            if listener.exception:
                raise listener.exception
            return listener.result
        finally:
            self.remove_listener(from_user=to, phone_id=recipient)

    def remove_listener(
        self: WhatsApp, from_user: str | int, phone_id: str | int | None = None
    ) -> None:
        """
        Remove and cancel a listener

        Args:
            from_user: The user that the listener is listening to
            phone_id: The phone id that the listener is listening for

        Raises:
            ValueError: If the listener does not exist
        """

        recipient = helpers.resolve_phone_id_param(self, phone_id, "phone_id")
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
