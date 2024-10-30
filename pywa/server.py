"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

import json
import logging
import threading
from typing import TYPE_CHECKING, Callable, cast

from . import utils, handlers, errors
from .handlers import (
    Handler,
    ChatOpenedHandler,
    TemplateStatusHandler,
    EncryptedFlowRequestType,
)  # noqa
from .handlers import (
    CallbackButtonHandler,
    CallbackSelectionHandler,
    MessageHandler,
    MessageStatusHandler,
    RawUpdateHandler,
    FlowCompletionHandler,
)
from .types import (
    MessageType,
    Message,
    TemplateStatus,
    MessageStatus,
    CallbackButton,
    CallbackSelection,
    FlowCompletion,
    ChatOpened,
)
from .types.base_update import (
    BaseUpdate,
    StopHandling,
    ContinueHandling,
    BaseUserUpdate,
)  # noqa

from .utils import FastAPI, Flask

if TYPE_CHECKING:
    from .client import WhatsApp


_MESSAGE_TYPES: dict[MessageType, type[Handler]] = {
    MessageType.BUTTON: CallbackButtonHandler,
    MessageType.REQUEST_WELCOME: ChatOpenedHandler,
}
_INTERACTIVE_TYPES: dict[str, type[Handler]] = {
    "button_reply": CallbackButtonHandler,
    "list_reply": CallbackSelectionHandler,
    "nfm_reply": FlowCompletionHandler,
}


_logger = logging.getLogger(__name__)


class Server:
    """This class is used internally by the :class:`WhatsApp` client to set up a webhook for receiving incoming
    requests."""

    _handlers_to_update_constractor: dict[
        type[Handler], Callable[["WhatsApp", dict], BaseUpdate]
    ] = {
        MessageHandler: Message.from_update,
        MessageStatusHandler: MessageStatus.from_update,
        CallbackButtonHandler: CallbackButton.from_update,
        CallbackSelectionHandler: CallbackSelection.from_update,
        ChatOpenedHandler: ChatOpened.from_update,
        FlowCompletionHandler: FlowCompletion.from_update,
        TemplateStatusHandler: TemplateStatus.from_update,
    }
    """A dictionary that maps handler types to their respective update constructors."""

    def __init__(
        self: "WhatsApp",
        server: Flask | FastAPI | None,
        webhook_endpoint: str,
        callback_url: str | None,
        webhook_fields: tuple[str, ...] | None,
        app_id: int | None,
        app_secret: str | None,
        verify_token: str | None,
        webhook_challenge_delay: int | None,
        business_private_key: str | None,
        business_private_key_password: str | None,
        flows_request_decryptor: utils.FlowRequestDecryptor | None,
        flows_response_encryptor: utils.FlowResponseEncryptor | None,
        continue_handling: bool,
        skip_duplicate_updates: bool,
        validate_updates: bool,
    ):
        self._server = server
        self._verify_token = verify_token
        self._webhook_endpoint = webhook_endpoint
        self._private_key = business_private_key
        self._private_key_password = business_private_key_password
        self._flows_request_decryptor = flows_request_decryptor
        self._app_id = app_id
        self._app_secret = app_secret
        self._flows_response_encryptor = flows_response_encryptor
        self._validate_updates = validate_updates
        self._continue_handling = continue_handling
        self._skip_duplicate_updates = skip_duplicate_updates
        self._updates_ids_in_process = set[
            str | int
        ]()  # TODO use threading.Lock | asyncio.Lock

        if server is utils.MISSING:
            return
        self._server_type = utils.ServerType.from_app(server)

        if not verify_token:
            raise ValueError(
                "When listening for incoming updates, a verify token must be provided.\n>> The verify token can "
                "be any string. It is used to challenge the webhook endpoint to verify that the endpoint is valid."
            )
        if validate_updates and not app_secret:
            _logger.warning(
                "No `app_secret` provided. Signature validation will be disabled "
                "(not recommended. set `validate_updates=False` to suppress this warning)"
            )
            self._validate_updates = False

        self._register_routes()

        if callback_url is not None:
            if app_id is None or app_secret is None:
                raise ValueError(
                    "When registering a callback URL, the app ID and app secret must be provided.\n>> See here how "
                    "to get them: "
                    "https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/"
                )

            self._delayed_register_callback_url(
                callback_url=f"{callback_url.rstrip('/')}/{self._webhook_endpoint.lstrip('/')}",
                app_id=app_id,
                app_secret=app_secret,
                verify_token=verify_token,
                fields=tuple(webhook_fields or Handler._fields_to_subclasses().keys()),
                delay=webhook_challenge_delay,
            )

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
                self._webhook_endpoint,
            )
            return ch, 200
        _logger.error(
            "Webhook ('%s') failed the verification challenge. Expected verify_token: %s, received: %s",
            self._webhook_endpoint,
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
        res, status, update_dict, update_hash = self._check_and_prepare_update(
            update=update, hmac_header=hmac_header
        )
        if res:
            return res, status
        self._call_handlers(update_dict)
        return self._after_calling_update(update_hash)

    def _check_and_prepare_update(
        self, update: bytes, hmac_header: str = None
    ) -> tuple[str | None, int | None, dict | None, str | None]:
        if self._validate_updates:
            if not hmac_header:
                _logger.debug(
                    "Webhook ('%s') received an update without a signature",
                    self._webhook_endpoint,
                )
                return "Error, missing signature", 401, None, None
            if not utils.webhook_updates_validator(
                app_secret=self._app_secret,
                request_body=update,
                x_hub_signature=hmac_header,
            ):
                _logger.debug(
                    "Webhook ('%s') received an update with an invalid signature",
                    self._webhook_endpoint,
                )
                return "Error, invalid signature", 401, None, None
        try:
            update_dict: dict = json.loads(update)
        except (TypeError, ValueError):
            _logger.debug(
                "Webhook ('%s') received non-JSON data: %s",
                self._webhook_endpoint,
                update,
            )
            return "Error, invalid update", 400, None, None

        update_hash: str | int | None = None
        _logger.debug(
            "Webhook ('%s') received an update: %s",
            self._webhook_endpoint,
            update_dict,
        )
        if self._skip_duplicate_updates and (
            update_hash := (hmac_header or hash(update))
        ):
            if update_hash in self._updates_ids_in_process:
                return "ok", 200, None, None
            self._updates_ids_in_process.add(update_hash)

        return None, None, update_dict, update_hash

    def _after_calling_update(self, update_hash: str | None) -> tuple[str, int]:
        if self._skip_duplicate_updates:
            try:
                self._updates_ids_in_process.remove(update_hash)
            except KeyError:
                pass
        return "ok", 200

    def _register_routes(self: "WhatsApp") -> None:
        match self._server_type:
            case utils.ServerType.FLASK:
                _logger.info("Using Flask with WSGI")
                import flask

                @self._server.route(self._webhook_endpoint, methods=["GET"])
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                def pywa_challenge() -> tuple[str, int]:
                    """Automatically generated by pywa to handle the verification challenge."""
                    return self.webhook_challenge_handler(
                        vt=flask.request.args.get(utils.HUB_VT),
                        ch=flask.request.args.get(utils.HUB_CH),
                    )

                @self._server.route(self._webhook_endpoint, methods=["POST"])
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                def pywa_webhook() -> tuple[str, int]:
                    """Automatically generated by pywa to handle incoming updates."""
                    return self.webhook_update_handler(
                        update=flask.request.data,
                        hmac_header=flask.request.headers.get(utils.HUB_SIG),
                    )

            case utils.ServerType.FASTAPI:
                _logger.info("Using FastAPI")
                import fastapi

                @self._server.get(self._webhook_endpoint)
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                def pywa_challenge(
                    vt: str = fastapi.Query(alias=utils.HUB_VT, example="xyzxyz"),
                    ch: str = fastapi.Query(alias=utils.HUB_CH, example="1858252904"),
                ) -> fastapi.Response:
                    """Automatically generated by pywa to handle the verification challenge."""
                    content, status_code = self.webhook_challenge_handler(
                        vt=vt,
                        ch=ch,
                    )
                    return fastapi.Response(
                        content=content,
                        status_code=status_code,
                        media_type="text/plain",
                    )

                async def _get_body(request: fastapi.Request):
                    return await request.body()

                @self._server.post(self._webhook_endpoint)
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                def pywa_webhook(
                    update: bytes = fastapi.Depends(_get_body),
                    hmac_header: str = fastapi.Header(
                        alias=utils.HUB_SIG, example="sha256=..."
                    ),
                ) -> fastapi.Response:
                    """Automatically generated by pywa to handle incoming updates."""
                    content, status_code = self.webhook_update_handler(
                        update=update,
                        hmac_header=hmac_header,
                    )
                    return fastapi.Response(
                        content=content,
                        status_code=status_code,
                        media_type="text/plain",
                    )
            case None:
                _logger.info("Using a custom server")

            case _:
                raise ValueError(
                    f"The `server` must be one of {utils.ServerType.protocols_names()} or None for a custom server"
                )

    def _call_handlers(self: "WhatsApp", update: dict) -> None:
        """Call the handlers for the given update."""
        try:
            try:
                handler_type = self._get_handler(update)
            except (KeyError, ValueError, TypeError, IndexError):
                (_logger.error if self._validate_updates else _logger.debug)(
                    "Webhook ('%s') received unexpected update%s: %s",
                    self._webhook_endpoint,
                    " (Enable `validate_updates` to ignore updates with invalid data)"
                    if not self._validate_updates
                    else "",
                    update,
                )
                handler_type = None

            if handler_type is None:
                return
            try:
                constructed_update = self._handlers_to_update_constractor[handler_type](
                    self, update
                )
                if constructed_update:
                    if handler_type._is_user_update and self._process_listener(
                        cast(BaseUserUpdate, constructed_update)
                    ):
                        return
                    self._invoke_callbacks(handler_type, constructed_update)
            except Exception:
                _logger.exception("Failed to construct update: %s", update)
        finally:
            # Always call raw update handler last
            self._call_raw_update_handler(update)

    def _call_raw_update_handler(self: "WhatsApp", update: dict) -> None:
        """Invoke the raw update handler."""
        self._invoke_callbacks(RawUpdateHandler, update)

    def _invoke_callbacks(
        self: "WhatsApp", handler_type: type[Handler], update: BaseUpdate | dict
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

    def _process_listener(self: "WhatsApp", update: BaseUserUpdate) -> bool:
        """Process and answer a listener if present."""
        listener = self._listeners.get(update.listener_identifier)
        if not listener:
            return False

        try:
            if listener.apply_filters(self, update):
                listener.set_result(update)
                return True
            elif listener.apply_cancelers(self, update):
                listener.cancel(update)
                return True
        except Exception as e:
            listener.set_exception(e)

        return not self._continue_handling

    def _get_handler(self: "WhatsApp", update: dict) -> type[Handler] | None:
        """Get the handler for the given update."""
        field = update["entry"][0]["changes"][0]["field"]
        value = update["entry"][0]["changes"][0]["value"]

        # The `messages` field needs to be handled differently because it can be a message, button, selection, or status
        # This check must return handler or None *BEFORE* getting the handler from the dict!!
        if field == "messages":
            if self.filter_updates and (
                value["metadata"]["phone_number_id"] != self.phone_id
            ):
                return None

            if "messages" in value:
                msg_type = value["messages"][0]["type"]
                if msg_type == MessageType.INTERACTIVE:
                    try:
                        interactive_type = value["messages"][0]["interactive"]["type"]
                    except KeyError:  # value with errors, when a user tries to send the interactive msg again
                        return MessageHandler
                    if (
                        handler := _INTERACTIVE_TYPES.get(interactive_type)
                    ) is not None:
                        return handler
                    _logger.warning(
                        "Webhook ('%s'): Unknown interactive message type: %s. Falling back to MessageHandler.",
                        self._webhook_endpoint,
                        interactive_type,
                    )
                return _MESSAGE_TYPES.get(msg_type, MessageHandler)

            elif "statuses" in value:  # status
                return MessageStatusHandler

            _logger.warning(
                "Webhook ('%s'): Unknown message type: %s",
                self._webhook_endpoint,
                value,
            )
            return None

        # noinspection PyProtectedMember
        return Handler._fields_to_subclasses().get(field)

    def _delayed_register_callback_url(
        self: "WhatsApp",
        callback_url: str,
        app_id: int,
        app_secret: str,
        verify_token: str,
        fields: tuple[str, ...] | None,
        delay: int,
    ) -> None:
        threading.Timer(
            interval=delay,
            function=self._register_callback_url,
            kwargs=dict(
                callback_url=callback_url,
                app_id=app_id,
                app_secret=app_secret,
                verify_token=verify_token,
                fields=fields,
            ),
        ).start()

    def _register_callback_url(
        self: "WhatsApp",
        callback_url: str,
        app_id: int,
        app_secret: str,
        verify_token: str,
        fields: tuple[str, ...] | None,
    ) -> None:
        """
        This is a non-blocking function that registers the callback URL.
        It must be called after the server is running so that the challenge can be verified.
        """
        try:
            app_access_token = self.api.get_app_access_token(
                app_id=app_id, app_secret=app_secret
            )
            if not self.api.set_app_callback_url(
                app_id=app_id,
                app_access_token=app_access_token["access_token"],
                callback_url=callback_url,
                verify_token=verify_token,
                fields=fields,
            )["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info("Callback URL '%s' registered successfully", callback_url)
        except errors.WhatsAppError as e:
            raise RuntimeError(
                f"Failed to register callback URL '{callback_url}'. if you are using a slow/custom server, you can "
                "increase the delay using the `webhook_challenge_delay` parameter when initializing the WhatsApp client."
            ) from e

    def get_flow_request_handler(
        self: "WhatsApp",
        endpoint: str,
        callback: handlers._FlowRequestHandlerT,
        acknowledge_errors: bool = True,
        handle_health_check: bool = True,
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
            handle_health_check: Whether to handle health checks (The callback will not be called for health checks).
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
            handle_health_check=handle_health_check,
            private_key=private_key,
            private_key_password=private_key_password,
            request_decryptor=request_decryptor,
            response_encryptor=response_encryptor,
        )

    def _register_flow_endpoint_callback(
        self: "WhatsApp",
        endpoint: str,
        callback: handlers._FlowRequestHandlerT,
        acknowledge_errors: bool,
        handle_health_check: bool,
        private_key: str | None,
        private_key_password: str | None,
        request_decryptor: utils.FlowRequestDecryptor | None,
        response_encryptor: utils.FlowResponseEncryptor | None,
    ) -> handlers.FlowRequestCallbackWrapper:
        """Internal function to register a flow endpoint callback."""
        if self._server is None:
            raise ValueError(
                "When using a custom server, you must use the `get_flow_request_handler` method to get the flow "
                "request handler and call it manually."
            )
        elif self._server is utils.MISSING:
            raise ValueError(
                "You must initialize the WhatsApp client with an web server"
                f" ({utils.ServerType.protocols_names()}) in order to handle incoming flow requests."
            )

        return self._register_flow_callback_wrapper(
            self.get_flow_request_handler(
                endpoint=endpoint,
                callback=callback,
                acknowledge_errors=acknowledge_errors,
                handle_health_check=handle_health_check,
                private_key=private_key,
                private_key_password=private_key_password,
                request_decryptor=request_decryptor,
                response_encryptor=response_encryptor,
            ),
        )

    def _register_flow_callback_wrapper(
        self: "WhatsApp",
        callback_wrapper: handlers.FlowRequestCallbackWrapper,
    ) -> handlers.FlowRequestCallbackWrapper:
        """Register the flow callback wrapper to the server."""
        match self._server_type:
            case utils.ServerType.FLASK:
                import flask

                @self._server.route(callback_wrapper._endpoint, methods=["POST"])
                @utils.rename_func(f"('{callback_wrapper._endpoint}')")
                def pywa_flow() -> tuple[str, int]:
                    """Automatically generated by pywa to handle incoming flow requests."""
                    return callback_wrapper.handle(flask.request.json)

            case utils.ServerType.FASTAPI:
                import fastapi

                @self._server.post(callback_wrapper._endpoint)
                @utils.rename_func(f"('{callback_wrapper._endpoint}')")
                def pywa_flow(
                    flow_req: EncryptedFlowRequestType,
                ) -> fastapi.Response:
                    """Automatically generated by pywa to handle incoming flow requests."""
                    response, status_code = callback_wrapper.handle(flow_req)
                    return fastapi.Response(
                        content=response,
                        status_code=status_code,
                    )

        return callback_wrapper
