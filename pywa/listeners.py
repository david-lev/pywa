from __future__ import annotations

__all__ = [
    "ListenerCanceled",
    "ListenerStopped",
    "ListenerTimeout",
    "TemplateStatusUpdateListenerIdentifier",
    "UserUpdateListenerIdentifier",
]

import dataclasses
import logging
import threading
import warnings
from typing import TYPE_CHECKING, Any, TypeVar, cast

from . import utils
from .errors import PywaWarning

if TYPE_CHECKING:
    from .client import WhatsApp
    from .filters import Filter
    from .types.base_update import BaseUpdate, BaseUserUpdate


@dataclasses.dataclass(frozen=True, kw_only=True)
class BaseListenerIdentifier: ...


@dataclasses.dataclass(frozen=True, kw_only=True)
class UserUpdateListenerIdentifier(BaseListenerIdentifier):
    sender: str
    recipient: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class TemplateStatusUpdateListenerIdentifier(BaseListenerIdentifier):
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
                        sender="123456", recipient="654321"
                    ),
                    filters=filters.message & filters.text,
                    cancelers=filters.callback_button & filters.matches("cancel"),
                )
            except ListenerCanceled as e:
                assert (
                    e.update.data == "cancel"
                )  # the update that caused the listener to be canceled
                wa.send_message(
                    "123456",
                    "You cancelled the listener by clicking the `cancel` button",
                )

    Attributes:
        update: The update that caused the listener to be canceled
    """

    update: BaseUpdate | BaseUserUpdate | None

    def __init__(self, update: BaseUpdate | BaseUserUpdate | None = None):
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
                print(e.reason)  # print the reason the listener was stopped
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


_logger = logging.getLogger(__name__)

_UpdateT = TypeVar("_UpdateT", bound="BaseUpdate")


class Listener:
    _listener_canceled = ListenerCanceled

    def __init__(
        self,
        filters: Filter[Any] | None,
        cancelers: Filter[Any] | None,
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
        self.set_exception(self._listener_canceled(update))

    def stop(self, reason: str | None = None) -> None:
        self.set_exception(ListenerStopped(reason))

    def is_set(self) -> bool:
        return self.event.is_set()

    def apply_filters(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return not self.filters or self.filters.check_sync(wa, update)

    def apply_cancelers(self, wa: WhatsApp, update: BaseUpdate) -> bool:
        return bool(self.cancelers) and self.cancelers.check_sync(wa, update)


def _warn_anyio_thread_limit(wa: WhatsApp) -> None:
    from . import server

    if wa._server_type in {
        utils.CustomServerType.STARLETTE,
        utils.CustomServerType.FASTAPI,
    }:
        current_active = len(wa._listeners)
        warning_threshold = max(1, int((server.ANYIO_THREADS_LIMIT or 40) * 0.90))

        if current_active < warning_threshold:
            wa._listeners_near_thread_limit = False
            return
        if wa._listeners_near_thread_limit:
            return
        wa._listeners_near_thread_limit = True

        _logger.warning(
            "%d active listeners are close to the AnyIO thread limit (%d): if it is reached the server "
            "will freeze and drop webhooks. Use `pywa_async`, set shorter `timeout`s on `.wait_for_...` "
            "calls, or raise the limit (%s).",
            current_active,
            server.ANYIO_THREADS_LIMIT or 40,
            "`pywa.server.ANYIO_THREADS_LIMIT`"
            if wa._server_type == utils.CustomServerType.STARLETTE
            else "in your app, then set `pywa.server.ANYIO_THREADS_LIMIT` to the same value",
        )


class _Listeners:
    def listen(
        self: WhatsApp,
        to: BaseListenerIdentifier,
        *,
        filters: Filter[_UpdateT] | None = None,
        cancelers: Filter[Any] | None = None,
        timeout: float | None = None,
    ) -> _UpdateT:
        """
        Listen to an update.

        - You can use one of the shortcuts to listen to a specific update type:
            - :meth:`~pywa.types.sent_update.SentMessage.wait_for_reply`
            - :meth:`~pywa.types.sent_update.SentMessage.wait_for_click`
            - :meth:`~pywa.types.sent_update.SentMessage.wait_for_selection`
            - :meth:`~pywa.types.sent_update.SentMessage.wait_for_completion`
            - :meth:`~pywa.types.sent_update.SentMessage.wait_until_read`
            - :meth:`~pywa.types.sent_update.SentMessage.wait_until_delivered`
            - :meth:`~pywa.types.template.CreatedTemplate.wait_until_approved`

        Example:

            .. code-block:: python

                    try:
                        wa.send_message(
                            to="123456",
                            text="Send me a message",
                            buttons=[Button(title="Cancel", callback_data="cancel")],
                        )
                        update: Message = wa.listen(
                            to=UserUpdateListenerIdentifier(
                                sender="123456", recipient="654321"
                            ),
                            filters=filters.message & filters.text,
                            cancelers=filters.callback_button
                            & filters.matches("cancel"),
                            timeout=10,
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
        if self._uvicorn_workers > 1:
            raise RuntimeError(
                "Listening is not supported when running on multiple workers"
            )
        if timeout is None:
            warnings.warn(
                "Listening without a `timeout` is highly discouraged as it can lead to memory leaks if the listener is never stopped.",
                PywaWarning,
                stacklevel=3,
            )
        _warn_anyio_thread_limit(self)
        self._check_for_async_filters(filters)
        self._check_for_async_filters(cancelers)

        listener = Listener(
            filters=filters,
            cancelers=cancelers,
        )
        self._listeners[to] = listener
        _logger.debug(
            "Listening for %r (timeout=%s, active listeners=%d)",
            to,
            timeout,
            len(self._listeners),
        )
        try:
            if not listener.event.wait(timeout):
                assert timeout is not None  # `.wait(None)` never times out
                _logger.info(
                    "Listener timed out after %ss (active listeners=%d)",
                    timeout,
                    len(self._listeners) - 1,
                )
                raise ListenerTimeout(timeout) from None

            if listener.exception:
                raise listener.exception

            assert listener.result is not None
            return cast("_UpdateT", listener.result)
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
            raise ValueError("Listener does not exist") from None
        listener.stop(reason)
        _logger.debug("Stopped listener %r (reason=%s)", to, reason)
        self._remove_listener(identifier=to)

    def _remove_listener(self: WhatsApp, identifier: BaseListenerIdentifier) -> None:
        try:
            del self._listeners[identifier]
        except KeyError:
            pass
