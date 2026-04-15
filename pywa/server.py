"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

import logging
import threading
from typing import TYPE_CHECKING, Any, Callable

from . import _helpers as helpers
from . import errors, handlers, utils
from .types import MessageType, RawUpdate, UserPreferenceCategory
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
    SystemType.USER_CHANGED_USER_ID: handlers.PhoneNumberChangeHandler,  # That's the new system message type for phone number changes, according to BSUID documentation
    "customer_changed_number": handlers.PhoneNumberChangeHandler,  # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#messages-object
    SystemType.CUSTOMER_IDENTITY_CHANGED: handlers.IdentityChangeHandler,
}
_INTERACTIVE_TYPES: dict[str, type[handlers.Handler]] = {
    "button_reply": handlers.CallbackButtonHandler,
    "list_reply": handlers.CallbackSelectionHandler,
    "nfm_reply": handlers.FlowCompletionHandler,
    "call_permission_reply": handlers.CallPermissionUpdateHandler,
}
_CALL_EVENTS: dict[str, type[handlers.Handler]] = {
    "connect": handlers.CallConnectHandler,
    "terminate": handlers.CallTerminateHandler,
}


_logger = logging.getLogger(__name__)


class Server:
    """This class is used internally by the :class:`WhatsApp` client to set up a webhook for receiving incoming
    requests."""

    def __init__(
        self: "WhatsApp",
    ):
        self._updates_in_process = set[
            str | int
        ]()  # TODO use threading.Lock | asyncio.Lock

        self._server_type = utils.CustomServerType.from_app(self.server)
        if self._server_type is not None:
            self._register_routes()

    def run(
        self: "WhatsApp", *, host: str = "127.0.0.1", port: int = 8000, **options: Any
    ) -> None:
        """
        Run the server to listen for incoming updates.

        Args:
            host: The host to listen on (default: ``127.0.0.1``)
            port: The port to listen on (default: ``8000``)
            **options: Additional options to pass to ``uvicorn.run`` (e.g. ``ssl_keyfile``, ``ssl_certfile``, etc.). See the `uvicorn documentation <https://uvicorn.dev/settings/>`_ for more details.
        """
        if self._server_type is not None:
            raise ValueError(
                "When providing a custom `server`, you must run it yourself."
            )
        try:
            from starlette.applications import Starlette as StarletteApp
        except ImportError:
            raise ImportError(
                'Starlette is required to run the server. Please install it using `pip install "pywa[server"]`.'
            ) from None

        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                'Uvicorn is required to run the server. Please install it using `pip install "pywa[server"]`.'
            ) from None

        self.server, self._server_type = (
            StarletteApp(),
            utils.CustomServerType.STARLETTE,
        )
        self._register_routes()

        uvicorn.run(
            self.server,
            host=host,
            port=port,
            headers=[
                ("server", "pywa"),
                ("X-Content-Type-Options", "nosniff"),
            ],
            **options,
        )
        exit()

    def webhook_challenge_handler(self, vt: str, ch: str) -> tuple[str, int]:
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
            _logger.info(
                "Webhook ('%s') passed the verification challenge",
                self.webhook_endpoint,
            )
            return ch, 200
        _logger.error(
            "Webhook ('%s') failed the verification challenge. Expected verify_token: %s, received: %s",
            self.webhook_endpoint,
            self._verify_token,
            vt,
        )
        return "Error, invalid verification token", 403

    def webhook_update_handler(
        self, update: bytes, hmac_header: str = None
    ) -> tuple[str, int]:
        """
        Handle the incoming update from the webhook manually.

        - Use this function only if you are using a custom server (e.g. Django etc.).

        Args:
            update: The incoming raw update from the webhook (bytes)
            hmac_header: The ``X-Hub-Signature-256`` header (to validate the signature, use ``utils.HUB_SIG`` for the key).

        Returns:
            A tuple containing the response and the status code.
        """
        res, status, raw_update, update_hash = self._check_and_prepare_update(
            update=update, hmac_header=hmac_header
        )
        if res:
            return res, status
        self._call_handlers(raw_update)
        return self._after_handling_update(update_hash)

    def _check_and_prepare_update(
        self, update: bytes, hmac_header: str = None
    ) -> tuple[str | None, int | None, RawUpdate | None, str | None]:
        if self._validate_updates:
            if not hmac_header:
                _logger.debug(
                    "Webhook ('%s') received an update without a signature",
                    self.webhook_endpoint,
                )
                return "Error, missing signature", 401, None, None
            if not utils.webhook_updates_validator(
                app_secret=self._app_secret,
                request_body=update,
                x_hub_signature=hmac_header,
            ):
                _logger.debug(
                    "Webhook ('%s') received an update with unmatching signature: %s, update: %s",
                    self.webhook_endpoint,
                    hmac_header,
                    update,
                )
                return "Unmatching signature", 200, None, None
        try:
            raw_update = RawUpdate(update, hmac_header=hmac_header)
        except (TypeError, ValueError):
            _logger.debug(
                "Webhook ('%s') received non-JSON data: %s",
                self.webhook_endpoint,
                update,
            )
            return "Error, invalid update", 400, None, None

        update_hash = hmac_header or hash(update)
        _logger.debug(
            "Webhook ('%s') received an update: %s",
            self.webhook_endpoint,
            raw_update,
        )
        if self._skip_duplicate_updates:
            if update_hash in self._updates_in_process:
                return "ok", 200, None, None
            self._updates_in_process.add(update_hash)

        return None, None, raw_update, update_hash

    def _after_handling_update(self, update_hash: str) -> tuple[str, int]:
        if self._skip_duplicate_updates:
            try:
                self._updates_in_process.remove(update_hash)
            except KeyError:
                pass
        return "ok", 200

    def _register_routes(self: "WhatsApp") -> None:
        if not self._verify_token:
            raise ValueError(
                "When listening for incoming updates, a verify token must be provided.\n>> The verify token can "
                "be any string. It is used to challenge the webhook endpoint to verify that the endpoint is valid."
            )
        if self._validate_updates and not self._app_secret:
            _logger.warning(
                "No `app_secret` provided. Signature validation will be disabled "
                "(not recommended. set `validate_updates=False` to suppress this warning)"
            )
            self._validate_updates = False

        match self._server_type:
            case utils.CustomServerType.STARLETTE:
                _logger.info("Using Starlette")
                helpers.register_routes_starlette(wa=self)
            case utils.CustomServerType.FASTAPI:
                _logger.info("Using FastAPI")
                helpers.register_routes_fastapi(wa=self)
            case utils.CustomServerType.FLASK:
                _logger.info("Using Flask")
                helpers.register_routes_flask(wa=self)
            case _:
                raise ValueError(
                    f"The `server` must be one of {utils.CustomServerType.protocols_names()} or None for a custom server"
                )
        for wrapper in self._flow_handlers_to_register:
            self._register_flow_handler_wrapper(wrapper)
        self._flow_handlers_to_register.clear()
        if self._callback_url is not None:
            self._delayed_register_callback_url()

    def _call_handlers(self: "WhatsApp", raw_update: RawUpdate) -> None:
        """Call the handlers for the given update."""
        try:
            try:
                handler_type = self._get_handler_type(raw_update)
            except (KeyError, ValueError, TypeError, IndexError):
                (_logger.error if self._validate_updates else _logger.debug)(
                    "Webhook ('%s') received unexpected update%s: %s",
                    self.webhook_endpoint,
                    " (Enable `validate_updates` to ignore updates with invalid data)"
                    if not self._validate_updates
                    else "",
                    raw_update,
                )
                handler_type = None

            if handler_type is None:
                return
            try:
                constructed_update: BaseUpdate = self._handlers_to_updates[
                    handler_type
                ].from_update(client=self, update=raw_update)
                if self._process_listener(constructed_update):
                    return
                self._invoke_callbacks(handler_type, constructed_update)
            except Exception:
                _logger.exception("Failed to construct update: %s", raw_update)
        finally:
            # Always call raw update handler last
            self._call_raw_update_handler(raw_update)

    def _call_raw_update_handler(self: "WhatsApp", update: RawUpdate) -> None:
        """Invoke the raw update handler."""
        self._invoke_callbacks(handlers.RawUpdateHandler, update)

    def _invoke_callbacks(
        self: "WhatsApp",
        handler_type: type[handlers.Handler],
        update: BaseUpdate | RawUpdate,
    ) -> None:
        """Process and call registered handlers for the update."""
        for handler in self._handlers[handler_type]:
            try:
                handled = handler.handle(self, update)
            except StopHandling:
                break
            except ContinueHandling:
                continue
            except Exception:
                handled = True
                _logger.exception(
                    "An error occurred while '%s' was handling an update",
                    handler._callback.__name__,
                )
            if handled and not self._continue_handling:
                break

    def _process_listener(self: "WhatsApp", update: BaseUpdate) -> bool:
        """Process and answer a listener if present."""
        if not (listener_identifiers := update.listener_identifiers):
            return False
        for identifier in listener_identifiers:
            listener = self._listeners.get(identifier)
            if listener is not None:
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
            listener.set_exception(e)

        return not self._continue_handling

    def _get_handler_type(
        self: "WhatsApp", update: RawUpdate
    ) -> type[handlers.Handler] | None:
        """Get the handler for the given update."""

        if self.filter_updates and self.waba_id and update.id != self.waba_id:
            return None

        try:
            if (
                self.filter_updates
                and self.phone_id
                and update.value["metadata"]["phone_number_id"] != self.phone_id
            ):
                return None
        except KeyError:  # no metadata in update
            pass

        if update.field in _complex_fields_handlers:
            return _complex_fields_handlers[update.field](self, update.value)

        # noinspection PyProtectedMember
        return handlers.Handler._handled_fields().get(update.field)

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
                        "When registering a callback URL in the WABA scope, the `business_account_id` must be provided."
                    )
            case utils.CallbackURLScope.PHONE:
                if not self.phone_id:
                    raise ValueError(
                        "When registering a callback URL in the PHONE scope, the `phone_id` must be provided."
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
        try:
            match self._callback_url_scope:
                case utils.CallbackURLScope.APP:
                    app_access_token = self.api.get_app_access_token(
                        client_id=self._app_id, client_secret=self._app_secret
                    )
                    res = self.api.set_app_callback_url(
                        app_id=self._app_id,
                        access_token=app_access_token["access_token"],
                        callback_url=self._callback_url,
                        verify_token=self._verify_token,
                        fields=tuple(self._webhook_fields),
                    )
                case utils.CallbackURLScope.WABA:
                    res = self.api.set_waba_alternate_callback_url(
                        waba_id=self.waba_id,
                        override_callback_uri=self._callback_url,
                        verify_token=self._verify_token,
                    )
                case utils.CallbackURLScope.PHONE:
                    res = self.api.set_phone_alternate_callback_url(
                        override_callback_uri=self._callback_url,
                        verify_token=self._verify_token,
                        phone_id=self.phone_id,
                    )
                case _:
                    raise ValueError("Invalid callback URL scope")

            if not res["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info(
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
        callback: handlers._FlowRequestHandlerT,
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
    wa: "WhatsApp", value: dict
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'messages' field."""
    if "messages" in value:
        msg_type = value["messages"][0]["type"]
        if msg_type == MessageType.INTERACTIVE:
            try:
                interactive_type = value["messages"][0]["interactive"]["type"]
            except (
                KeyError
            ):  # value with errors, when a user tries to send the interactive msg again
                return handlers.MessageHandler
            if (handler := _INTERACTIVE_TYPES.get(interactive_type)) is not None:
                return handler
            _logger.warning(
                "Webhook ('%s'): Unknown interactive message type: %s. Falling back to MessageHandler.",
                wa.webhook_endpoint,
                interactive_type,
            )
        elif msg_type == MessageType.SYSTEM:
            system_type = value["messages"][0]["system"]["type"]

            if (handler := _SYSTEM_TYPES.get(system_type)) is not None:
                return handler
            _logger.warning(
                "Webhook ('%s'): Unknown system message type: %s. Falling back to MessageHandler.",
                wa.webhook_endpoint,
                system_type,
            )
        return _MESSAGE_TYPES.get(msg_type, handlers.MessageHandler)

    elif "statuses" in value:  # status
        if value["statuses"][0].get("recipient_type") == "group":
            return handlers.GroupMessageStatusesHandler
        return handlers.MessageStatusHandler

    _logger.warning(
        "Webhook ('%s'): Unknown message type: %s",
        wa.webhook_endpoint,
        value,
    )
    return None


def _handle_calls_field(wa: "WhatsApp", value: dict) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'calls' field."""
    if "calls" in value:
        if (handler := _CALL_EVENTS.get(value["calls"][0]["event"])) is not None:
            return handler
        _logger.warning(
            "Webhook ('%s'): Unknown call event: %s.",
            wa.webhook_endpoint,
            value["calls"][0]["event"],
        )
    elif "statuses" in value:
        return handlers.CallStatusHandler
    return None


def _handle_user_preferences_field(
    wa: "WhatsApp", value: dict
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'user_preferences' field."""
    if (
        value["user_preferences"][0]["category"]
        == UserPreferenceCategory.MARKETING_MESSAGES
    ):
        return handlers.UserMarketingPreferencesHandler
    _logger.warning(
        "Webhook ('%s'): Unknown user preference category: %s.",
        wa.webhook_endpoint,
        value["user_preferences"][0]["category"],
    )
    return None


def _handle_smb_message_echoes_field(
    wa: "WhatsApp", value: dict
) -> type[handlers.Handler] | None:
    """Handle webhook updates with 'smb_message_echoes' field."""
    return _OUTGOING_MESSAGE_TYPES.get(
        value["message_echoes"][0]["type"], handlers.OutgoingMessageHandler
    )


_complex_fields_handlers: dict[
    str, Callable[["WhatsApp", dict], type[handlers.Handler] | None]
] = {
    "messages": _handle_messages_field,
    "calls": _handle_calls_field,
    "user_preferences": _handle_user_preferences_field,
    "smb_message_echoes": _handle_smb_message_echoes_field,
}
