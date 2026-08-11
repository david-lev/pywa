"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

import contextlib
import logging
import os
import threading
import time
import warnings
from collections import OrderedDict
from collections.abc import Callable
from typing import TYPE_CHECKING

from . import _helpers as helpers
from . import errors, handlers, utils
from ._logging import (
    ENV_LOG_LEVEL,
    bind_update_logger,
    format_banner,
    get_update_hash,
    setup_console_logging,
)
from .errors import PywaDeprecationWarning, PywaWarning
from .types import AccountUpdate, MessageType, RawUpdate, UserPreferenceCategory
from .types.base_update import (
    BaseUpdate,
    ContinueHandling,
    StopHandling,
)
from .types.system import SystemType

if TYPE_CHECKING:
    from .client import WhatsApp

_MESSAGE_TYPES: dict[MessageType, type[handlers.Handler]] = {
    MessageType.BUTTON: handlers.CallbackButtonHandler,
    MessageType.EDIT: handlers.EditedMessageHandler,
    MessageType.REVOKE: handlers.DeletedMessageHandler,
}
_OUTGOING_MESSAGE_TYPES: dict[MessageType, type[handlers.Handler]] = {
    MessageType.EDIT: handlers.OutgoingEditedMessageHandler,
    MessageType.REVOKE: handlers.OutgoingDeletedMessageHandler,
}
_SYSTEM_TYPES: dict[SystemType | str, type[handlers.Handler]] = {
    SystemType.USER_CHANGED_NUMBER: handlers.PhoneNumberChangeHandler,
    SystemType.USER_CHANGED_USER_ID: handlers.PhoneNumberChangeHandler,
    # That's the new system message type for phone number changes, according to BSUID documentation
    "customer_changed_number": handlers.PhoneNumberChangeHandler,
    # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#messages-object
    SystemType.CUSTOMER_IDENTITY_CHANGED: handlers.IdentityChangeHandler,
}
_INTERACTIVE_TYPES: dict[str, type[handlers.Handler]] = {
    "button_reply": handlers.CallbackButtonHandler,
    "list_reply": handlers.CallbackSelectionHandler,
    "call_permission_reply": handlers.CallPermissionUpdateHandler,
}
_NFM_REPLY_TYPES: dict[str, type[handlers.Handler]] = {
    "flow": handlers.FlowCompletionHandler,
}
_CALL_EVENTS: dict[str, type[handlers.Handler]] = {
    "connect": handlers.CallConnectHandler,
    "terminate": handlers.CallTerminateHandler,
}

_logger = logging.getLogger(__name__)

MAX_PROCESSED_UPDATES = 100_000
ANYIO_THREADS_LIMIT: int | None = None


def _update_hash_of(update: BaseUpdate | RawUpdate) -> str | None:
    """Return the update hash for either a constructed update or a raw one, if available."""
    if isinstance(update, RawUpdate):
        return getattr(update, "_update_hash", None)
    return getattr(getattr(update, "raw", None), "_update_hash", None)


class Server:
    """This class is used internally by the :class:`WhatsApp` client to set up a webhook for receiving incoming
    requests."""

    def __init__(
        self: "WhatsApp",
    ):
        self._processed_updates: OrderedDict[str, None] = OrderedDict()
        self._cache_lock = threading.Lock()
        if self._server is not None:
            self._server_type = utils.CustomServerType.from_app(self._server)
            if self._server_type is not None:
                self._register_routes()
        else:
            self._server_type = None

    def _setup_and_get_starlette_app(self: "WhatsApp"):
        # This is the ASGI factory uvicorn calls to build the app - including fresh,
        # in a subprocess that re-imports everything, when running with `--reload` or
        # multiple workers. Configuring logging here (rather than only where `run()`/the
        # CLI are invoked) guarantees it's applied in the process that actually handles
        # requests, not just in a parent/reloader process that never sees any traffic.
        setup_console_logging(os.environ.get(ENV_LOG_LEVEL, "info"))
        if self._server_type is not None:
            raise ValueError(
                "When providing a custom `server` instance to the WhatsApp client, pywa assumes you will handle the webhook routes and server setup yourself. "
            )
        try:
            from starlette.applications import Starlette as StarletteApp
        except ImportError:
            raise ImportError(
                'Starlette is required to run the built-in server. Please install it using `pip install "pywa[server]"`.'
            ) from None

        if ANYIO_THREADS_LIMIT is not None:
            thread_limit = ANYIO_THREADS_LIMIT

            @contextlib.asynccontextmanager
            async def lifespan(_: StarletteApp):
                from anyio.to_thread import current_default_thread_limiter

                current_default_thread_limiter().total_tokens = thread_limit
                _logger.debug(
                    "Set AnyIO default thread limiter to %d threads",
                    thread_limit,
                )
                yield
        else:
            lifespan = None

        self._server, self._server_type = (
            StarletteApp(lifespan=lifespan),
            utils.CustomServerType.STARLETTE,
        )
        self._register_routes()
        return self._server

    def run(
        self: "WhatsApp",
        *,
        host: str = "127.0.0.1",
        port: int = 8000,
        log_level: str | int = "info",
    ) -> None:
        """
        Run the server to listen for incoming webhooks.

        This method starts a basic, blocking server for quick prototyping and
        testing. It does not support advanced development features such as
        hot-reloading.

        For a richer developer experience (like auto-reloading on code changes)
        and to prepare for cloud deployments, it is highly recommended to use
        the ``pywa`` CLI instead of this method.

        Example CLI Usage:

            .. code-block:: bash

                $ pywa dev bot.py

        Args:
            host: The host address to bind the server to (default: ``127.0.0.1``).
            port: The port number to listen on (default: ``8000``).
            log_level: The console log level for pywa's own logs and uvicorn's logs
             (default: ``"info"``). One of ``"critical"``, ``"error"``, ``"warning"``,
             ``"info"``, ``"debug"`` or ``"trace"``. Debug/trace output may include
             personal data from your users (phone numbers, names, message content) -
             avoid enabling it in production.
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "Uvicorn are required to run the built-in server. "
                'Please install it using `pip install "pywa[server]"`.'
            ) from None

        # `log_level` is not passed to uvicorn.run(): uvicorn's own
        # Config.configure_logging() would use it to re-set uvicorn.error/access/asgi,
        # clobbering the pinned levels setup_console_logging() (called below, via the
        # ASGI factory) just applied.
        os.environ[ENV_LOG_LEVEL] = str(log_level)
        app = self._setup_and_get_starlette_app()
        _logger.info(
            format_banner(
                [
                    "🚀  Starting Pywa server",
                    f"🌐  Server URL:   http://{host}:{port}",
                    f"📝  Log Level:    {log_level}",
                    (
                        "💡  Tip:          Use the `pywa` CLI (`pywa dev`/`pywa run`) for hot-reload, "
                        "multi-worker support and other features (`pywa run --help`)"
                    ),
                ]
            )
        )
        uvicorn.run(
            app=app,
            host=host,
            port=port,
            log_config=None,
            access_log=False,
        )

    def webhook_challenge_handler(
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
        if vt == self._verify_token:
            _logger.debug(
                "[%s] Passed verification challenge",
                self._webhook_endpoint,
            )
            return ch, 200
        _logger.warning(
            "[%s] Failed verification challenge: invalid verify token",
            self._webhook_endpoint,
        )
        return "Forbidden", 403

    def webhook_update_validator(
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
        if not self._validate_updates:
            return None

        if not hmac_header:
            _logger.warning(
                "[%s] Rejected an update without a signature",
                self._webhook_endpoint,
            )
            return "Unauthorized", 401

        assert (
            self._app_secret is not None
        )  # guaranteed when `_validate_updates` is True
        if not utils.webhook_updates_validator(
            app_secret=self._app_secret,
            request_body=update,
            x_hub_signature=hmac_header,
        ):
            _logger.warning(
                "[%s] Received an update with unmatching signature: '%s'",
                self._webhook_endpoint,
                hmac_header,
            )
            return "Forbidden", 403

        return None

    def webhook_update_handler(
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
            error_response = self.webhook_update_validator(update, hmac_header)
            if error_response:
                return error_response

        update_hash = get_update_hash(update)
        log = bind_update_logger(_logger, update_hash, self._webhook_endpoint)
        try:
            raw_update = RawUpdate(
                update, hmac_header=hmac_header, update_hash=update_hash
            )
        except (TypeError, ValueError):
            _logger.warning(
                "[%s] Rejected a malformed (non-JSON) update body (%d bytes)",
                self._webhook_endpoint,
                len(update) if hasattr(update, "__len__") else -1,
            )
            if _logger.isEnabledFor(logging.DEBUG):
                preview = (
                    update[:200]
                    if isinstance(update, (bytes, bytearray))
                    else str(update)[:200]
                )
                _logger.debug("[%s] preview=%r", self._webhook_endpoint, preview)
            return "Bad Request", 400

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Received raw update: %s", raw_update)

        if self._skip_duplicate_updates:
            with self._cache_lock:
                if update_hash in self._processed_updates:
                    log.info("Skipped duplicate update")
                    return "ok", 200

                self._processed_updates[update_hash] = None

                if len(self._processed_updates) > MAX_PROCESSED_UPDATES:
                    self._processed_updates.popitem(last=False)

        self._call_handlers(raw_update)

        return "ok", 200

    def _register_routes(self: "WhatsApp") -> None:
        if not self._verify_token:
            raise ValueError(
                "When listening for incoming updates, a `verify_token` must be provided.\n>> The verify token can "
                "be any string. It is used to challenge the webhook endpoint to verify that the endpoint is valid."
            )
        if self._validate_updates and not self._app_secret:
            warnings.warn(
                message="No `app_secret` provided. Signature validation will be disabled "
                "(not recommended! set `validate_updates=False` to suppress this warning)",
                category=PywaWarning,
                stacklevel=1,
            )
            self._validate_updates = False

        match self._server_type:
            case utils.CustomServerType.STARLETTE:
                _logger.debug(
                    "Registered Starlette routes at %s", self._webhook_endpoint
                )
                helpers.register_routes_starlette(wa=self)
            case utils.CustomServerType.FASTAPI:
                _logger.debug("Registered FastAPI routes at %s", self._webhook_endpoint)
                helpers.register_routes_fastapi(wa=self)
            case utils.CustomServerType.FLASK:
                _logger.debug("Registered Flask routes at %s", self._webhook_endpoint)
                helpers.register_routes_flask(wa=self)
            case _:
                raise ValueError(
                    f"The `server` must be one of {utils.CustomServerType.protocols_names()}, but got {type(self._server)}"
                )
        for wrapper in self._flow_handlers_to_register:
            _logger.debug(
                "Registered flow request handler at %s%s",
                self._webhook_endpoint,
                wrapper._endpoint,
            )
            self._register_flow_handler_wrapper(wrapper)
        self._flow_handlers_to_register.clear()
        if self._callback_url is not None:
            self._delayed_register_callback_url()

    def _call_handlers(self: "WhatsApp", raw_update: RawUpdate) -> None:
        """Call the handlers for the given update."""
        log = bind_update_logger(
            _logger, raw_update._update_hash, self._webhook_endpoint
        )
        start = time.perf_counter()
        handler_type: type[handlers.Handler] | None = None
        try:
            try:
                handler_type = self._get_handler_type(raw_update)
            except (KeyError, ValueError, TypeError, IndexError):
                log_fn = log.error if self._validate_updates else log.debug
                log_fn(
                    "Received unexpected update%s: field=%s waba_id=%s",
                    ""
                    if self._validate_updates
                    else " (Enable `validate_updates` to ignore updates with invalid data)",
                    raw_update.field,
                    raw_update.id,
                )
                handler_type = None

            if handler_type is None:
                log.debug("No handler resolved for update (field=%s)", raw_update.field)
                return
            log.debug("Dispatched to %s", handler_type.__name__)
            try:
                constructed_update: BaseUpdate = self._handlers_to_updates[
                    handler_type
                ].from_update(client=self, update=raw_update)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug("Constructed update: %s", constructed_update)
                if self._process_listener(constructed_update):
                    return
                self._invoke_callbacks(handler_type, constructed_update)
            except Exception:
                log.exception("Failed to construct update (field=%s)", raw_update.field)
        finally:
            # Always call raw update handler last
            self._call_raw_update_handler(raw_update)
            log.info(
                "Finished processing update (handler=%s) in %.2fms",
                handler_type.__name__ if handler_type else None,
                (time.perf_counter() - start) * 1000,
            )

    def _call_raw_update_handler(self: "WhatsApp", update: RawUpdate) -> None:
        """Invoke the raw update handler."""
        self._invoke_callbacks(handlers.RawUpdateHandler, update)

    def _invoke_callbacks(
        self: "WhatsApp",
        handler_type: type[handlers.Handler],
        update: BaseUpdate | RawUpdate,
    ) -> None:
        """Process and call registered handlers for the update."""
        log = bind_update_logger(
            _logger, _update_hash_of(update), self._webhook_endpoint
        )
        for handler in self._handlers[handler_type]:
            callback_name = getattr(
                handler._callback, "__name__", repr(handler._callback)
            )
            try:
                log.debug("Checking if handler %s should handle the update", handler)
                checked_update = handler.check(self, update)
                if checked_update is None:
                    continue
                log.debug("Calling '%s'", callback_name)
                handler._callback(self, checked_update)
                handled = True
            except StopHandling:
                log.debug("Stopped further handling after '%s'", callback_name)
                break
            except ContinueHandling:
                log.debug("Continued further handling after '%s'", callback_name)
                continue
            except Exception:
                handled = True
                log.exception(
                    "Error occurred while '%s' was handling the update",
                    callback_name,
                )
            if handled and not self._continue_handling:
                log.debug("Stopped further handling after '%s'", callback_name)
                break
            log.debug("Continued further handling after '%s'", callback_name)

    def _process_listener(self: "WhatsApp", update: BaseUpdate) -> bool:
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
            if listener.apply_filters(self, update):
                listener.set_result(update)
                return not self._continue_handling
            elif listener.apply_cancelers(self, update):
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

    def _get_handler_type(
        self: "WhatsApp", update: RawUpdate
    ) -> type[handlers.Handler] | None:
        """Get the handler for the given update."""
        update_field = update.field
        log = bind_update_logger(_logger, update._update_hash, self._webhook_endpoint)
        account_id = (
            self.waba_id
            if update_field != AccountUpdate._webhook_field
            else self.business_portfolio_id
        )
        if self.filter_updates and account_id and update.id != account_id:
            log.debug(
                "Filtered out update (ID: %s) because it doesn't match the Client's waba_id",
                update.id,
            )
            return None

        try:
            if (
                self.filter_updates
                and self.phone_id
                and (received_phone_id := update.value["metadata"]["phone_number_id"])
                != self.phone_id
            ):
                log.debug(
                    "Filtered out update because phone_id mismatch: %s != %s",
                    received_phone_id,
                    self.phone_id,
                )
                return None
        except KeyError:  # no metadata in update
            pass

        if update_field in _complex_fields_handlers:
            return _complex_fields_handlers[update_field](self, update)

        # noinspection PyProtectedMember
        return handlers.Handler._handled_fields().get(update_field)

    def _delayed_register_callback_url(
        self: "WhatsApp",
    ) -> None:
        match self._callback_url_scope:
            case utils.CallbackURLScope.APP:
                if self._app_id is None or self._app_secret is None:
                    raise ValueError(
                        "When registering a callback URL in the app scope, the `app_id` and `app_secret` must be provided.\n>> See here how "
                        "to get them: "
                        "https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/"
                    )
            case utils.CallbackURLScope.WABA:
                if not self.waba_id:
                    raise ValueError(
                        "When registering a callback URL in the `WABA` scope, the `waba_id` must be provided."
                    )
            case utils.CallbackURLScope.PHONE:
                if not self.phone_id:
                    raise ValueError(
                        "When registering a callback URL in the `PHONE` scope, the `phone_id` must be provided."
                    )
        _logger.debug(
            "Registering callback URL '%s' in scope '%s' after a delay of %s seconds to allow the server to start and be ready to receive the verification challenge.",
            self._callback_url,
            self._callback_url_scope.name,
            self._webhook_challenge_delay,
        )
        threading.Timer(
            interval=self._webhook_challenge_delay,
            function=self._register_callback_url,
        ).start()

    def _register_callback_url(
        self: "WhatsApp",
    ) -> None:
        """
        This is a non-blocking function that registers the callback URL.
        It must be called after the server is running so that the challenge can be verified.
        """
        assert self._callback_url is not None
        assert self._verify_token is not None
        try:
            match self._callback_url_scope:
                case utils.CallbackURLScope.APP:
                    assert self._app_id is not None
                    assert self._app_secret is not None
                    app_access_token = self.api.get_app_access_token(
                        client_id=int(self._app_id),
                        client_secret=self._app_secret,
                    )
                    res = self.api.set_app_callback_url(
                        app_id=int(self._app_id),
                        access_token=app_access_token["access_token"],
                        callback_url=self._callback_url,
                        verify_token=self._verify_token,
                        fields=tuple(self._webhook_fields),
                    )
                case utils.CallbackURLScope.WABA:
                    assert self.waba_id is not None
                    res = self.api.set_waba_alternate_callback_url(
                        waba_id=str(self.waba_id),
                        override_callback_uri=self._callback_url,
                        verify_token=self._verify_token,
                    )
                case utils.CallbackURLScope.PHONE:
                    assert self.phone_id is not None
                    res = self.api.set_phone_alternate_callback_url(
                        override_callback_uri=self._callback_url,
                        verify_token=self._verify_token,
                        phone_id=str(self.phone_id),
                    )
                case _:
                    raise ValueError("Invalid callback URL scope")

            if not res["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.debug(
                "Callback URL '%s' registered successfully", self._callback_url
            )
        except errors.WhatsAppError as e:
            raise RuntimeError(
                f"Failed to register callback URL '{self._callback_url}'. if you are using a slow/custom server, you can "
                "increase the delay using the `webhook_challenge_delay` parameter when initializing the WhatsApp client."
            ) from e

    def get_flow_request_handler(
        self: "WhatsApp",
        endpoint: str,
        callback: handlers._FlowRequestCallback,
        acknowledge_errors: bool = True,
        private_key: str | None = None,
        private_key_password: str | None = None,
        request_decryptor: utils.FlowRequestDecryptor | None = None,
        response_encryptor: utils.FlowResponseEncryptor | None = None,
    ) -> handlers.FlowRequestCallbackWrapper:
        """
        Get a function that handles the incoming flow requests.

        - Use this function only if you are using a custom server (e.g. Django etc.), else use the
          :meth:`WhatsApp.on_flow_request` decorator.

        Args:
            endpoint: The endpoint to listen to (The endpoint uri you set to the flow. e.g ``/feedback_flow``).
            callback: The callback function to call when a flow request is received.
            acknowledge_errors: Whether to acknowledge errors (The return value of the callback will be ignored, and
             pywa will acknowledge the error automatically).
            private_key: The private key to use to decrypt the requests (Override the global ``business_private_key``).
            private_key_password: The password to use to decrypt the private key (Override the global ``business_private_key_password``).
            request_decryptor: The function to use to decrypt the requests (Override the global ``flows_request_decryptor``)
            response_encryptor: The function to use to encrypt the responses (Override the global ``flows_response_encryptor``)

        Returns:
            A function that handles the incoming flow request and returns (response, status_code).
        """
        return handlers.FlowRequestCallbackWrapper(
            wa=self,
            endpoint=endpoint,
            callback=callback,
            acknowledge_errors=acknowledge_errors,
            private_key=private_key,
            private_key_password=private_key_password,
            request_decryptor=request_decryptor,
            response_encryptor=response_encryptor,
        )

    def _register_flow_handler_wrapper(
        self: "WhatsApp",
        callback_wrapper: handlers.FlowRequestCallbackWrapper,
    ) -> handlers.FlowRequestCallbackWrapper:
        """Register the flow callback wrapper to the server."""
        match self._server_type:
            case utils.CustomServerType.STARLETTE:
                helpers.register_flow_endpoint_starlette(
                    wa=self, callback_wrapper=callback_wrapper
                )
            case utils.CustomServerType.FASTAPI:
                helpers.register_flow_endpoint_fastapi(
                    wa=self, callback_wrapper=callback_wrapper
                )
            case utils.CustomServerType.FLASK:
                helpers.register_flow_endpoint_flask(
                    wa=self, callback_wrapper=callback_wrapper
                )

        return callback_wrapper


def _handle_messages_field(
    wa: "WhatsApp", update: RawUpdate
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'messages' field."""
    value = update.value
    log = bind_update_logger(_logger, update._update_hash, wa._webhook_endpoint)
    if "messages" in value:
        msg_type = value["messages"][0]["type"]
        if msg_type == MessageType.INTERACTIVE:
            try:
                interactive_type = value["messages"][0]["interactive"]["type"]
            except KeyError:  # value has `errors`, when a user tries to send the interactive msg again
                return handlers.MessageHandler
            if (handler := _INTERACTIVE_TYPES.get(interactive_type)) is not None:
                return handler
            if interactive_type == "nfm_reply":
                return _NFM_REPLY_TYPES.get(
                    value["messages"][0]["interactive"]["nfm_reply"]["name"]
                )
            log.warning(
                "Unknown interactive message type: %s. Fell back to MessageHandler.",
                interactive_type,
            )
        elif msg_type == MessageType.SYSTEM:
            system_type = value["messages"][0]["system"]["type"]

            if (handler := _SYSTEM_TYPES.get(system_type)) is not None:
                return handler
            log.warning(
                "Unknown system message type: %s. Fell back to MessageHandler.",
                system_type,
            )
        return _MESSAGE_TYPES.get(msg_type, handlers.MessageHandler)

    elif "statuses" in value:  # status
        if value["statuses"][0].get("recipient_type") == "group":
            return handlers.GroupMessageStatusesHandler
        return handlers.MessageStatusHandler

    if log.isEnabledFor(logging.DEBUG):
        log.debug("Unrecognized update payload: %s", value)
    else:
        log.warning("Received update with unrecognized shape (keys=%s)", list(value))
    return None


def _handle_calls_field(
    wa: "WhatsApp", update: RawUpdate
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'calls' field."""
    value = update.value
    log = bind_update_logger(_logger, update._update_hash, wa._webhook_endpoint)
    if "calls" in value:
        if (handler := _CALL_EVENTS.get(value["calls"][0]["event"])) is not None:
            return handler
        log.warning("Unknown call event: %s.", value["calls"][0]["event"])
    elif "statuses" in value:
        return handlers.CallStatusHandler
    return None


def _handle_user_preferences_field(
    wa: "WhatsApp", update: RawUpdate
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'user_preferences' field."""
    value = update.value
    if (
        value["user_preferences"][0]["category"]
        == UserPreferenceCategory.MARKETING_MESSAGES
    ):
        return handlers.UserMarketingPreferencesHandler
    log = bind_update_logger(_logger, update._update_hash, wa._webhook_endpoint)
    log.warning(
        "Unknown user preference category: %s.",
        value["user_preferences"][0]["category"],
    )
    return None


def _handle_smb_message_echoes_field(
    wa: "WhatsApp", update: RawUpdate
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'smb_message_echoes' field."""
    value = update.value
    return _OUTGOING_MESSAGE_TYPES.get(
        value["message_echoes"][0]["type"], handlers.OutgoingMessageHandler
    )


_complex_fields_handlers: dict[
    str, Callable[["WhatsApp", RawUpdate], type[handlers.Handler] | None]
] = {
    "messages": _handle_messages_field,
    "calls": _handle_calls_field,
    "user_preferences": _handle_user_preferences_field,
    "smb_message_echoes": _handle_smb_message_echoes_field,
}
