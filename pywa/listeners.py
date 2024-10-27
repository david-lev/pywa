from __future__ import annotations

__all__ = [
    "ListenerTimeout",
    "ListenerCanceled",
    "ListenerStopped",
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
    """
    The listener timed out

    Example:

        .. code-block:: python

                try:
                    wa.listen(to="123456", timeout=10)
                except ListenerTimeout as e:
                    wa.send_message("123456", "Timeout")

    Attributes:
        timeout: The timeout that was set for the listener
    """

    def __init__(self, timeout: int):
        self.timeout = timeout


class ListenerCanceled(Exception):
    """
    The listener was canceled by a filter

    Example:

        .. code-block:: python

            try:
                wa.listen(
                    to="123456",
                    filters=filters.message & filters.text,
                    cancelers=filters.callback_button & filters.matches("cancel")
                )
            except ListenerCanceled as e:
                print(e.update) # print the update that caused the listener to be canceled
                wa.send_message("123456", "You cancelled the listener by clicking the cancel button")

    Attributes:
        update: The update that caused the listener to be canceled
    """

    def __init__(self, update: BaseUserUpdate | None = None):
        self.update = update


class ListenerStopped(Exception):
    """
    The listener was stopped manually by wa.stop_listening(...)

    Example:

        .. code-block:: python

            try:
                wa.listen("123456")
            except ListenerStopped as e:
                print(e.reason) # print the reason the listener was stopped
                wa.send_message("123456", "The listener was stopped")

    Attributes:
        reason: The reason the listener was stopped (set by wa.stop_listening(reason="..."))
    """

    def __init__(self, reason: str | None = None):
        self.reason = reason


class Listener:
    _listener_canceled = ListenerCanceled

    def __init__(
        self,
        filters: Filter,
        cancelers: Filter,
    ):
        self.filters = filters
        self.cancelers = cancelers
        self.event: threading.Event = threading.Event()
        self.result: _SuppoertedUserUpdate | None = None
        self.exception: Exception | None = None

    def set_result(self, result: BaseUserUpdate) -> None:
        self.result = result
        self.event.set()

    def set_exception(self, exception: Exception) -> None:
        self.exception = exception
        self.event.set()

    def cancel(self, update: BaseUserUpdate | None = None) -> None:
        self.set_exception(self._listener_canceled(update))

    def stop(self, reason: str | None = None) -> None:
        self.set_exception(ListenerStopped(reason))

    def is_set(self) -> bool:
        return self.event.is_set()

    def apply_filters(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        return self.filters is None or self.filters.check_sync(wa, update)

    def apply_cancelers(self, wa: WhatsApp, update: _SuppoertedUserUpdate) -> bool:
        return self.cancelers and self.cancelers.check_sync(wa, update)


class Listeners:
    def listen(
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
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_reply`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_click`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_selection`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_until_read`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_until_delivered`

        Example:

            .. code-block:: python

                    try:
                        wa.send_message(
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
        identifier = utils.listener_identifier(sender=to, recipient=recipient)
        listener = Listener(
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[identifier] = listener
        try:
            if not listener.event.wait(timeout):
                raise ListenerTimeout(timeout)
            if listener.result:
                return listener.result
            if listener.exception:
                raise listener.exception
        finally:
            self._remove_listener(from_user=to, phone_id=recipient)

    def stop_listening(
        self: WhatsApp,
        to: str | int,
        reason: str | None = None,
        phone_id: str | int | None = None,
    ) -> None:
        """
        Stop listening to a user.
            - Raising :class:`ListenerStopped` to the listener

        Args:
            to: The user that the listener is listening to
            reason: The reason to stop listening
            phone_id: The phone id that the listener is listening for

        Raises:
            ValueError: If the listener does not exist
        """

        recipient = helpers.resolve_phone_id_param(self, phone_id, "phone_id")
        try:
            listener = self._listeners[
                utils.listener_identifier(sender=to, recipient=recipient)
            ]
        except KeyError:
            raise ValueError("Listener does not exist")
        listener.stop(reason)
        self._remove_listener(from_user=to, phone_id=recipient)

    def _remove_listener(
        self: WhatsApp, from_user: str | int, phone_id: str | int | None = None
    ) -> None:
        recipient = helpers.resolve_phone_id_param(self, phone_id, "phone_id")
        try:
            del self._listeners[
                utils.listener_identifier(sender=from_user, recipient=recipient)
            ]
        except KeyError:
            pass
