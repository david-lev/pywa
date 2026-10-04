import asyncio
import copy
import logging
import time
import warnings
from typing import TYPE_CHECKING

from pywa._logging import (
    TRACE,
    bind_update_logger,
    compact_repr,
    describe_raw_update,
    describe_update,
    get_update_hash,
)
from pywa.server import _logger, _update_hash_of
from pywa.types.base_update import BaseUpdate

from . import errors, utils
from .errors import PywaDeprecationWarning
from .handlers import (
    Handler,
    RawUpdateHandler,
)
from .types import (
    ContinueHandling,
    RawUpdate,
    StopHandling,
)

if TYPE_CHECKING:
    from pywa_async import WhatsApp

MAX_PROCESSED_UPDATES = 100_000


class Server:
    async def webhook_challenge_handler(
        self: "WhatsApp", vt: str | None, ch: str | None
    ) -> tuple[str | None, int]:
        """
        Handle the verification challenge from the webhook manually.

        - Use this function only if you are using a custom server (e.g. Django etc.).

        Args:
            vt: The verify token param (utils.HUB_VT).
            ch: The challenge param (utils.HUB_CH).

        Returns:
            A tuple containing the challenge and the status code.
        """
        return super().webhook_challenge_handler(vt=vt, ch=ch)

    async def webhook_update_validator(
        self: "WhatsApp", update: bytes, hmac_header: str | None
    ) -> tuple[str, int] | None:
        """
        Validate the incoming webhook update signature.

        Args:
            update: The incoming raw update from the webhook (bytes)
            hmac_header: The ``X-Hub-Signature-256`` header (to validate the signature, use ``utils.HUB_SIG`` for the key).

        Returns:
            A tuple of (error_message, status_code) if validation fails, otherwise None.
        """
        return super().webhook_update_validator(update=update, hmac_header=hmac_header)

    async def webhook_update_handler(
        self: "WhatsApp", update: bytes, hmac_header: None = None
    ) -> tuple[str, int]:
        """
        Handle the incoming update manually.

        - Use this function only if you are using a custom server (e.g. Django etc.).

        Args:
            update: The incoming raw update from the webhook (bytes)
            hmac_header: Deprecated. Use ``client.webhook_update_validator`` to validate the request first.

        Returns:
            A tuple containing the response and the status code.
        """
        if hmac_header is not None:
            warnings.warn(
                "The `hmac_header` argument in `webhook_update_handler` is deprecated and will be removed "
                "in a future version. Use `client.webhook_update_validator` to validate the request first.",
                PywaDeprecationWarning,
                stacklevel=2,
            )
            error_response = await self.webhook_update_validator(update, hmac_header)
            if error_response:
                return error_response

        update_hash = get_update_hash(update)
        log = bind_update_logger(_logger, update_hash, self._webhook_endpoint)
        try:
            raw_update = RawUpdate(
                update, hmac_header=hmac_header, update_hash=update_hash
            )
        except (TypeError, ValueError):
            log.warning(
                "Rejected a malformed (non-JSON) update body (%d bytes)",
                len(update) if hasattr(update, "__len__") else -1,
            )
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Malformed body preview: %r", bytes(update[:200]))
            return "Bad Request", 400

        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "Received %s (%d bytes)", describe_raw_update(raw_update), len(update)
            )
        if log.isEnabledFor(TRACE):
            log.log(TRACE, "Raw payload: %s", bytes(update).decode(errors="replace"))

        if self._skip_duplicate_updates:
            if update_hash in self._processed_updates:
                log.info("Skipped duplicate update")
                return "ok", 200

            self._processed_updates[update_hash] = None

            if len(self._processed_updates) > MAX_PROCESSED_UPDATES:
                self._processed_updates.popitem(last=False)

        await self._call_handlers(raw_update)

        return "ok", 200

    async def _call_handlers(self: "WhatsApp", raw_update: RawUpdate) -> None:
        """Call the handlers for the given update."""
        log = bind_update_logger(
            _logger, raw_update._update_hash, self._webhook_endpoint
        )
        start = time.perf_counter()
        handler_type: type[Handler] | None = None
        constructed_update: BaseUpdate | None = None
        called: list[str] = []
        try:
            try:
                handler_type = self._get_handler_type(raw_update)
            except (KeyError, ValueError, TypeError, IndexError):
                log_fn = log.error if self._validate_updates else log.debug
                log_fn(
                    "Received unexpected update%s: %s",
                    ""
                    if self._validate_updates
                    else " (Enable `validate_updates` to ignore updates with invalid data)",
                    describe_raw_update(raw_update),
                )
                handler_type = None

            if handler_type is None:
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(
                        "No handler type resolved for %s",
                        describe_raw_update(raw_update),
                    )
                return
            log.debug("Resolved handler type %s", handler_type.__name__)
            try:
                constructed_update = self._handlers_to_updates[
                    handler_type
                ].from_update(client=self, update=raw_update)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug("Parsed update: %s", compact_repr(constructed_update))
                if await self._process_listener(constructed_update):
                    called.append("<listener>")
                    return
                called += await self._invoke_callbacks(handler_type, constructed_update)
            except Exception:
                log.exception(
                    "Failed to process update (%s)", describe_raw_update(raw_update)
                )
        finally:
            # Always call raw update handler last
            called += await self._call_raw_update_handler(raw_update)
            what = (
                describe_update(constructed_update)
                if constructed_update is not None
                else describe_raw_update(raw_update)
            )
            elapsed = (time.perf_counter() - start) * 1000
            if called:
                log.info("%s -> %s (%.1fms)", what, ", ".join(called), elapsed)
            else:
                log.info("%s -> no handler matched (%.1fms)", what, elapsed)

    async def _call_raw_update_handler(
        self: "WhatsApp", update: RawUpdate
    ) -> list[str]:
        """Invoke the raw update handler."""
        return await self._invoke_callbacks(RawUpdateHandler, update)

    async def _invoke_callbacks(
        self: "WhatsApp", handler_type: type[Handler], update: BaseUpdate | RawUpdate
    ) -> list[str]:
        """Process and call registered handlers for the update, returning the called callbacks' names."""
        log = bind_update_logger(
            _logger, _update_hash_of(update), self._webhook_endpoint
        )
        called: list[str] = []
        for handler in self._handlers[handler_type]:
            callback_name = getattr(
                handler._callback, "__name__", repr(handler._callback)
            )
            try:
                checked_update = await handler.acheck(self, update)
                if checked_update is None:
                    log.debug("Filters of '%s' did not match", callback_name)
                    continue
                log.debug("Calling '%s'", callback_name)
                called.append(callback_name)
                call_start = time.perf_counter()
                await handler._callback(
                    self, checked_update
                ) if handler._is_async_callback else handler._callback(
                    self, checked_update
                )
                handled = True
                log.debug(
                    "'%s' finished in %.1fms",
                    callback_name,
                    (time.perf_counter() - call_start) * 1000,
                )
            except StopHandling:
                log.debug("Stopped further handling after '%s'", callback_name)
                break
            except ContinueHandling:
                log.debug("Continued further handling after '%s'", callback_name)
                continue
            except Exception:
                handled = True
                called[-1] = f"{callback_name} (raised)"
                log.exception(
                    "Error occurred while '%s' was handling the update",
                    callback_name,
                )
            if handled and not self._continue_handling:
                break
        return called

    async def _process_listener(self: "WhatsApp", update: BaseUpdate) -> bool:
        """Process and answer a listener if present."""
        if not (listener_identifiers := update.listener_identifiers):
            return False
        raw = getattr(update, "raw", None)
        log = (
            bind_update_logger(_logger, raw._update_hash, self._webhook_endpoint)
            if raw is not None
            else _logger
        )
        for identifier in listener_identifiers:
            listener = self._listeners.get(identifier)
            if listener is not None:
                log.debug("Found matching listener")
                break
        else:
            return False

        try:
            if await listener.apply_filters(self, update):
                listener.set_result(update)
                return not self._continue_handling
            elif await listener.apply_cancelers(self, update):
                listener.cancel(update)
                return not self._continue_handling
            else:
                return False  # if no filters or cancelers matched, continue handling
        except ContinueHandling:
            return False
        except StopHandling:
            return True
        except Exception as e:
            log.exception("Exception while processing listener")
            listener.set_exception(e)

        return not self._continue_handling

    def _register_callback_url(
        self: "WhatsApp",
    ) -> None:
        """
        This is a non-blocking function that registers the callback URL.
        It must be called after the server is running so that the challenge can be verified.
        """
        loop = asyncio.new_event_loop()
        api = copy.copy(self.api)
        api._session = self._httpx_client(  # TODO: copy the session properly
            timeout=api._session.timeout,
            base_url=api._session.base_url,
            headers=api._session.headers,
        )

        assert self._callback_url is not None
        assert self._verify_token is not None
        try:
            match self._callback_url_scope:
                case utils.CallbackURLScope.APP:
                    assert self._app_id is not None
                    assert self._app_secret is not None
                    app_access_token = loop.run_until_complete(
                        api.get_app_access_token(
                            client_id=int(self._app_id),
                            client_secret=self._app_secret,
                        )
                    )
                    res = loop.run_until_complete(
                        api.set_app_callback_url(
                            app_id=int(self._app_id),
                            access_token=app_access_token["access_token"],
                            callback_url=self._callback_url,
                            verify_token=self._verify_token,
                            fields=tuple(self._webhook_fields),
                        )
                    )
                case utils.CallbackURLScope.WABA:
                    assert self.waba_id is not None
                    res = loop.run_until_complete(
                        api.set_waba_alternate_callback_url(
                            waba_id=str(self.waba_id),
                            override_callback_uri=self._callback_url,
                            verify_token=self._verify_token,
                        )
                    )
                case utils.CallbackURLScope.PHONE:
                    assert self.phone_id is not None
                    res = loop.run_until_complete(
                        api.set_phone_alternate_callback_url(
                            override_callback_uri=self._callback_url,
                            verify_token=self._verify_token,
                            phone_id=str(self.phone_id),
                        )
                    )
                case _:
                    raise ValueError("Invalid callback URL scope")

            if not res["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info(
                "Callback URL '%s' registered (scope=%s)",
                self._callback_url,
                self._callback_url_scope.name,
            )
        except errors.WhatsAppError as e:
            raise RuntimeError(
                f"Failed to register callback URL '{self._callback_url}'. if you are using a slow/custom server, you can "
                "increase the delay using the `webhook_challenge_delay` parameter when initializing the WhatsApp client."
            ) from e
