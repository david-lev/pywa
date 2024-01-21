"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Callable

from pywa import utils
from pywa.errors import WhatsAppError
from pywa.handlers import Handler, ChatOpenedHandler  # noqa
from pywa.handlers import (
    CallbackButtonHandler,
    CallbackSelectionHandler,
    MessageHandler,
    MessageStatusHandler,
    RawUpdateHandler,
    FlowCompletionHandler,
)
from pywa.types import MessageType, FlowRequest, FlowResponse
from pywa.types.base_update import BaseUpdate, StopHandling  # noqa
from pywa.types.flows import (
    FlowRequestCannotBeDecrypted,
    FlowResponseError,  # noqa
    FlowTokenNoLongerValid,
)
from pywa.utils import FastAPI, Flask

if TYPE_CHECKING:
    from pywa.client import WhatsApp

_VERIFY_TIMEOUT_SEC = 6


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

    def __init__(
        self: WhatsApp,
        server: Flask | FastAPI | None,
        webhook_endpoint: str,
        callback_url: str | None,
        fields: tuple[str, ...] | None,
        app_id: int | None,
        app_secret: str | None,
        verify_token: str | None,
        verify_timeout: int | None,
        business_private_key: str | None,
        business_private_key_password: str | None,
        flows_request_decryptor: utils.FlowRequestDecryptor | None,
        flows_response_encryptor: utils.FlowResponseEncryptor | None,
    ):
        if server is None:
            self._server = None
            return
        self._server = server
        self._webhook_endpoint = webhook_endpoint
        self._private_key = business_private_key
        self._private_key_password = business_private_key_password
        self._flows_request_decryptor = flows_request_decryptor
        self._flows_response_encryptor = flows_response_encryptor

        if not verify_token:
            raise ValueError(
                "When listening for incoming updates, a verify token must be provided.\n>> The verify token can "
                "be any string. It is used to challenge the webhook endpoint to verify that the endpoint is valid."
            )

        hub_vt = "hub.verify_token"
        hub_ch = "hub.challenge"

        if utils.is_flask_app(self._server):
            import flask

            @self._server.route(self._webhook_endpoint, methods=["GET"])
            @utils.rename_func(f"({self.phone_id})")
            def challenge() -> tuple[str, int]:
                if flask.request.args.get(hub_vt) == verify_token:
                    return flask.request.args.get(hub_ch), 200
                return "Error, invalid verification token", 403

            @self._server.route(self._webhook_endpoint, methods=["POST"])
            @utils.rename_func(f"({self.phone_id})")
            def webhook() -> tuple[str, int]:
                threading.Thread(
                    target=self._call_handlers,
                    args=(flask.request.json,),
                ).start()
                return "ok", 200

        elif utils.is_fastapi_app(self._server):
            import fastapi

            @self._server.get(self._webhook_endpoint)
            @utils.rename_func(f"({self.phone_id})")
            def challenge(
                vt: str = fastapi.Query(..., alias=hub_vt),
                ch: str = fastapi.Query(..., alias=hub_ch),
            ):
                if vt == verify_token:
                    return fastapi.Response(content=ch, status_code=200)
                return fastapi.Response(
                    content="Error, invalid verification token",
                    status_code=403,
                )

            @self._server.post(self._webhook_endpoint)
            @utils.rename_func(f"({self.phone_id})")
            def webhook(payload: dict = fastapi.Body(...)):
                threading.Thread(target=self._call_handlers, args=(payload,)).start()
                return fastapi.Response(content="ok", status_code=200)

        else:
            raise ValueError("The server must be a Flask or FastAPI app.")

        if callback_url is not None:
            if app_id is None or app_secret is None:
                raise ValueError(
                    "When registering a callback URL, the app ID and app secret must be provided.\n>> See here how "
                    "to get them: "
                    "https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/"
                )

            # This is a non-blocking function that registers the callback URL.
            # It must be called after the server is running so that the challenge can be verified.
            def register_callback_url() -> None:
                if verify_timeout is not None and verify_timeout > _VERIFY_TIMEOUT_SEC:
                    time.sleep(verify_timeout - _VERIFY_TIMEOUT_SEC)
                try:
                    app_access_token = self.api.get_app_access_token(
                        app_id=app_id, app_secret=app_secret
                    )
                    if not self.api.set_callback_url(
                        app_id=app_id,
                        app_access_token=app_access_token["access_token"],
                        callback_url=f"{callback_url}/{self._webhook_endpoint}",
                        verify_token=verify_token,
                        fields=tuple(
                            fields or Handler.__fields_to_subclasses__().keys()
                        ),
                    )["success"]:
                        raise RuntimeError("Failed to register callback URL.")
                except WhatsAppError as e:
                    raise RuntimeError("Failed to register callback URL.") from e

            threading.Thread(target=register_callback_url).start()

    def _call_handlers(self: WhatsApp, update: dict) -> None:
        """Call the handlers for the given update."""
        try:
            handler_type = self._get_handler(update=update)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
        ):  # this endpoint got non-expected data
            _logger.exception("Failed to get handler for update: %s" % update)
            return

        try:
            # noinspection PyCallingNonCallable
            constructed_update = handler_type.__update_constructor__(self, update)
        except Exception:
            _logger.exception("Failed to construct update: %s" % update)
            return

        for handler in self._handlers[handler_type]:
            try:
                # noinspection PyCallingNonCallable
                handler.handle(self, constructed_update)
            except Exception as e:
                if isinstance(e, StopHandling):
                    break
                _logger.exception(
                    "An error occurred while %s was handling an update"
                    % handler.callback.__name__,
                )
        for raw_update_handler in self._handlers[RawUpdateHandler]:
            try:
                raw_update_handler.handle(self, update)
            except Exception as e:
                if isinstance(e, StopHandling):
                    break
                _logger.exception(
                    "An error occurred while %s was handling an raw update"
                    % raw_update_handler.callback.__name__,
                )

    def _get_handler(self: WhatsApp, update: dict) -> type[Handler] | None:
        """Get the handler for the given update."""
        try:
            field = update["entry"][0]["changes"][0]["field"]
            value = update["entry"][0]["changes"][0]["value"]
        except (KeyError, IndexError, TypeError):  # this endpoint got non-expected data
            raise ValueError(f"Invalid update: {update}")

        # The `messages` field needs to be handled differently because it can be a message, button, selection, or status
        # This check must return handler or None *BEFORE* getting the handler from the dict!!
        if field == "messages":
            if not self.filter_updates or (
                value["metadata"]["phone_number_id"] == self.phone_id
            ):
                if "messages" in value:
                    msg_type = value["messages"][0]["type"]
                    if msg_type == MessageType.INTERACTIVE:
                        try:
                            interactive_type = value["messages"][0]["interactive"][
                                "type"
                            ]
                        except KeyError:  # value with errors, when a user tries to send the interactive msg again
                            return MessageHandler
                        if (
                            handler := _INTERACTIVE_TYPES.get(interactive_type)
                        ) is not None:
                            return handler
                        _logger.warning(
                            "PyWa Webhook: Unknown interactive message type: %s. Falling back to MessageHandler."
                            % interactive_type
                        )
                    return _MESSAGE_TYPES.get(msg_type, MessageHandler)

                elif "statuses" in value:  # status
                    return MessageStatusHandler
                _logger.warning("PyWa Webhook: Unknown message type: %s" % value)
            return None

        return Handler.__fields_to_subclasses__().get(field)

    def _register_flow_endpoint_callback(
        self: WhatsApp,
        endpoint: str,
        callback: Callable[
            [WhatsApp, FlowRequest], FlowResponse | FlowResponseError | dict | None
        ],
        acknowledge_errors: bool,
        handle_health_check: bool,
        private_key: str | None,
        private_key_password: str | None,
        request_decryptor: utils.FlowRequestDecryptor | None,
        response_encryptor: utils.FlowResponseEncryptor | None,
    ) -> None:
        """Internal function to register a flow endpoint callback."""
        if self._server is None:
            raise ValueError(
                "You must initialize the WhatsApp client with an web server"
                " (Flask or FastAPI) in order to handle incoming flow requests."
            )
        private_key = private_key or self._private_key
        private_key_password = private_key_password or self._private_key_password
        if not private_key:
            raise ValueError(
                "A private_key must be provided in order to decrypt incoming requests. You can provide it when "
                "initializing the WhatsApp client or when registering the flow request callback."
            )
        request_decryptor = request_decryptor or self._flows_request_decryptor
        if not request_decryptor:
            raise ValueError(
                "A `request_decryptor` must be provided in order to decrypt incoming requests. You can provide it when "
                "initializing the WhatsApp client or when registering the flow request callback."
            )
        response_encryptor = response_encryptor or self._flows_response_encryptor
        if not response_encryptor:
            raise ValueError(
                "A `response_encryptor` must be provided in order to encrypt outgoing responses. You can provide it "
                "when initializing the WhatsApp client or when registering the flow request callback."
            )
        if (
            request_decryptor is utils.default_flow_request_decryptor
            or response_encryptor is utils.default_flow_response_encryptor
        ) and not utils.is_cryptography_installed():
            raise ValueError(
                "The default decryptor/encryptor requires the `cryptography` package to be installed."
                '\n>> Install it with `pip install cryptography` / pip install "pywa[cryptography]"` or use a '
                "custom decryptor/encryptor."
            )
        if endpoint == self._webhook_endpoint:
            raise ValueError(
                "The flow endpoint cannot be the same as the webhook endpoint."
            )

        def flow_endpoint(payload: dict) -> tuple[str, int]:
            """The actual registered endpoint callback. returns response, status code"""
            try:
                decrypted_request, aes_key, iv = request_decryptor(
                    payload["encrypted_flow_data"],
                    payload["encrypted_aes_key"],
                    payload["initial_vector"],
                    private_key,
                    private_key_password,
                )
            except Exception:
                _logger.exception(
                    "Flow Endpoint (%s): Decryption failed for payload: %s"
                    % (endpoint, payload)
                )
                return "Decryption failed", FlowRequestCannotBeDecrypted.status_code
            if handle_health_check and decrypted_request["action"] == "ping":
                return response_encryptor(
                    {
                        "version": decrypted_request["version"],
                        "data": {"status": "active"},
                    },
                    aes_key,
                    iv,
                ), 200
            try:
                request = FlowRequest.from_dict(
                    data=decrypted_request, raw_encrypted=payload
                )
            except Exception:
                _logger.exception(
                    "Flow Endpoint (%s): Failed to construct FlowRequest from decrypted data: %s"
                    % (endpoint, decrypted_request)
                )
                return "Failed to construct FlowRequest", 500
            try:
                response = callback(self, request)
                if isinstance(response, FlowResponseError):
                    raise response
            except FlowTokenNoLongerValid as e:
                return (
                    response_encryptor(
                        {"error_msg": e.error_message},
                        aes_key,
                        iv,
                    ),
                    e.status_code,
                )
            except FlowResponseError as e:
                return e.__class__.__name__, e.status_code
            except Exception:
                _logger.exception(
                    "Flow Endpoint (%s): An error occurred while %s was handling a flow request"
                    % (endpoint, callback.__name__)
                )
                return "An error occurred", 500

            if acknowledge_errors and request.has_error:
                return response_encryptor(
                    {
                        "version": request.version,
                        "data": {
                            "acknowledged": True,
                        },
                    },
                    aes_key,
                    iv,
                ), 200
            if not isinstance(response, (FlowResponse | dict)):
                raise TypeError(
                    f"Flow endpoint callback must return a `FlowResponse` or `dict`, not {type(response)}"
                )
            return response_encryptor(
                response.to_dict() if isinstance(response, FlowResponse) else response,
                aes_key,
                iv,
            ), 200

        if utils.is_flask_app(self._server):
            import flask

            @self._server.route(endpoint, methods=["POST"])
            @utils.rename_func(f"({endpoint})")
            def flow() -> tuple[str, int]:
                return flow_endpoint(flask.request.json)

        elif utils.is_fastapi_app(self._server):
            import fastapi

            @self._server.post(endpoint)
            @utils.rename_func(f"({endpoint})")
            def flow(payload: dict = fastapi.Body(...)):
                response, status_code = flow_endpoint(payload)
                return fastapi.Response(
                    content=response,
                    status_code=status_code,
                )
