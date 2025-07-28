from __future__ import annotations

__all__ = [
    "ListenerTimeout",
    "ListenerCanceled",
    "ListenerStopped",
    "UserUpdateListenerIdentifier",
    "TemplateUpdateListenerIdentifier",
]

import dataclasses
import threading
from typing import TYPE_CHECKING

from . import utils

if TYPE_CHECKING:
    from .client import WhatsApp
    from .types.base_update import BaseUpdate
    from .filters import Filter


@dataclasses.dataclass(frozen=True, kw_only=True)
class BaseListenerIdentifier: ...


@dataclasses.dataclass(frozen=True, kw_only=True)
class UserUpdateListenerIdentifier(BaseListenerIdentifier):
    sender: str
    recipient: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class TemplateUpdateListenerIdentifier(BaseListenerIdentifier):
    waba_id: str
    template_id: str


class ListenerTimeout(Exception):
    """
    The listener timed out

    Example:

        .. code-block:: python

                try:
                    wa.listen(..., timeout=10)
                except ListenerTimeout as e:
                    wa.send_message(to="123456", text="You took too long to respond")

    Attributes:
        timeout: The timeout that was set for the listener
    """

    def __init__(self, timeout: float):
        self.timeout = timeout

    def __str__(self):
        return f"Listener timed out after {self.timeout} seconds"


class ListenerCanceled(Exception):
    """
    The listener was canceled by a filter

    Example:

        .. code-block:: python

            try:
                wa.listen(
                    to=UserUpdateListenerIdentifier(
                        sender="123456",
                        recipient="654321"
                    ),
                    filters=filters.message & filters.text,
                    cancelers=filters.callback_button & filters.matches("cancel")
                )
            except ListenerCanceled as e:
                assert e.update.data == "cancel" # the update that caused the listener to be canceled
                wa.send_message("123456", "You cancelled the listener by clicking the `cancel` button")

    Attributes:
        update: The update that caused the listener to be canceled
    """

    def __init__(self, update: BaseUpdate | None = None):
        self.update = update

    def __str__(self):
        return (
            f"Listener was canceled by update: {self.update}"
            if self.update
            else "Listener was canceled"
        )


class ListenerStopped(Exception):
    """
    The listener was stopped manually by wa.stop_listening(...)

    Example:

        .. code-block:: python

            try:
                wa.listen(...)
            except ListenerStopped as e:
                print(e.reason) # print the reason the listener was stopped
                wa.send_message("123456", "The listener was stopped")

    Attributes:
        reason: The reason the listener was stopped (set by `wa.stop_listening(reason="...")`)
    """

    def __init__(self, reason: str | None = None):
        self.reason = reason

    def __str__(self):
        return (
            f"Listener was stopped: {self.reason}"
            if self.reason
            else "Listener was stopped"
        )


class Listener:
    def __init__(
        self,
        filters: Filter,
        cancelers: Filter,
    ):
        self.filters = filters
        self.cancelers = cancelers
        self.event: threading.Event = threading.Event()
        self.result: BaseUpdate | None = None
        self.exception: Exception | None = None

    def set_result(self, result: BaseUpdate) -> None:
        self.result = result
        self.event.set()

    def set_exception(self, exception: Exception) -> None:
        self.exception = exception
        self.event.set()

    def cancel(self, update: BaseUpdate | None = None) -> None:
        self.set_exception(ListenerCanceled(update))

    def stop(self, reason: str | None = None) -> None:
        self.set_exception(ListenerStopped(reason))

    def is_set(self) -> bool:
        return self.event.is_set()

    def apply_filters(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return not self.filters or self.filters.check_sync(wa, update)

    def apply_cancelers(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return self.cancelers and self.cancelers.check_sync(wa, update)


class _Listeners:
    def listen(
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
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_reply`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_click`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_selection`
            - :meth:`~pywa.types.sent_message.SentMessage.wait_for_completion`
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
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[to] = listener
        try:
            if not listener.event.wait(timeout):
                raise ListenerTimeout(timeout)

            if listener.exception:
                raise listener.exception

            return listener.result
        finally:
            self._remove_listener(identifier=to)

    def stop_listening(
        self: WhatsApp,
        to: BaseListenerIdentifier,
        *,
        reason: str | None = None,
    ) -> None:
        """
        Stop listening to updates for a specific listener

            - Raising :class:`ListenerStopped` to the listener

        Args:
            to: The identifier of the listener to stop
            reason: The reason to stop listening

        Raises:
            ValueError: If the listener does not exist
        """

        try:
            listener = self._listeners[to]
        except KeyError:
            raise ValueError("Listener does not exist")
        listener.stop(reason)
        self._remove_listener(identifier=to)

    def _remove_listener(self: WhatsApp, identifier: BaseListenerIdentifier) -> None:
        try:
            del self._listeners[identifier]
        except KeyError:
            pass
