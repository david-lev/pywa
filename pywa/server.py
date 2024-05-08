"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

__all__ = ["Server"]

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Callable

from . import utils, handlers
from .errors import WhatsAppError
from .handlers import Handler, ChatOpenedHandler, TemplateStatusHandler  # noqa
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
    FlowRequest,
    FlowResponse,
    Message,
    TemplateStatus,
    MessageStatus,
    CallbackButton,
    CallbackSelection,
    FlowCompletion,
    ChatOpened,
)
from .types.base_update import BaseUpdate, StopHandling  # noqa
from .types.flows import (
    FlowRequestCannotBeDecrypted,
    FlowResponseError,  # noqa
    FlowTokenNoLongerValid,
)
from .utils import FastAPI, Flask

if TYPE_CHECKING:
    from .client import WhatsApp

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
        self: "WhatsApp",
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
        max_workers: int,
    ):
        if server is None:
            self._server = None
            return
        self._server = server
        self._server_type = utils.ServerType.from_app(server)
        self._executor = ThreadPoolExecutor(max_workers, thread_name_prefix="Handler")
        self._loop = asyncio.get_event_loop()
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
        self._register_routes(verify_token=verify_token)

        if callback_url is not None:
            if app_id is None or app_secret is None:
                raise ValueError(
                    "When registering a callback URL, the app ID and app secret must be provided.\n>> See here how "
                    "to get them: "
                    "https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/"
                )
            # noinspection PyProtectedMember
            self._delayed_register_callback_url(
                callback_url=f"{callback_url.rstrip('/')}/{self._webhook_endpoint.lstrip('/')}",
                app_id=app_id,
                app_secret=app_secret,
                verify_token=verify_token,
                fields=tuple(fields or Handler._fields_to_subclasses().keys()),
                delay=(verify_timeout - _VERIFY_TIMEOUT_SEC)
                if verify_timeout is not None and verify_timeout > _VERIFY_TIMEOUT_SEC
                else 0,
            )

    def _register_routes(self: "WhatsApp", verify_token: str) -> None:
        hub_vt = "hub.verify_token"
        hub_ch = "hub.challenge"

        async def challenge_handler(vt: str, ch: str) -> tuple[str, int]:
            """The challenge function that is called when the callback URL is registered."""
            if vt == verify_token:
                _logger.info(
                    "Webhook ('%s') passed the verification challenge",
                    self._webhook_endpoint,
                )
                return ch, 200
            _logger.error(
                "Webhook ('%s') failed the verification challenge. Expected verify_token: %s, received: %s",
                self._webhook_endpoint,
                verify_token,
                vt,
            )
            return "Error, invalid verification token", 403

        async def webhook_update_handler(update: dict) -> tuple[str, int]:
            """The webhook function that is called when an update is received."""
            _logger.debug(
                "Webhook ('%s') received an update: %s",
                self._webhook_endpoint,
                update,
            )

            await self._call_handlers(update)
            return "ok", 200

        match self._server_type:
            case utils.ServerType.FLASK:
                import flask

                if utils.is_installed("asgiref"):  # flask[async]

                    @self._server.route(self._webhook_endpoint, methods=["GET"])
                    @utils.rename_func(f"({self.phone_id})")
                    async def flask_challenge() -> tuple[str, int]:
                        return await challenge_handler(
                            vt=flask.request.args.get(hub_vt),
                            ch=flask.request.args.get(hub_ch),
                        )

                    @self._server.route(self._webhook_endpoint, methods=["POST"])
                    @utils.rename_func(f"({self.phone_id})")
                    async def flask_webhook() -> tuple[str, int]:
                        return await webhook_update_handler(flask.request.json)

                else:  # flask

                    @self._server.route(self._webhook_endpoint, methods=["GET"])
                    @utils.rename_func(f"({self.phone_id})")
                    def flask_challenge() -> tuple[str, int]:
                        return self._loop.run_until_complete(
                            challenge_handler(
                                vt=flask.request.args.get(hub_vt),
                                ch=flask.request.args.get(hub_ch),
                            )
                        )

                @self._server.route(self._webhook_endpoint, methods=["POST"])
                @utils.rename_func(f"({self.phone_id})")
                def flask_webhook() -> tuple[str, int]:
                    return self._loop.run_until_complete(
                        webhook_update_handler(flask.request.json)
                    )

            case utils.ServerType.FASTAPI:
                import fastapi

                @self._server.get(self._webhook_endpoint)
                @utils.rename_func(f"({self.phone_id})")
                async def fastapi_challenge(req: fastapi.Request) -> fastapi.Response:
                    content, status_code = await challenge_handler(
                        vt=req.query_params.get(hub_vt), ch=req.query_params.get(hub_ch)
                    )
                    return fastapi.Response(content=content, status_code=status_code)

                @self._server.post(self._webhook_endpoint)
                @utils.rename_func(f"({self.phone_id})")
                async def fastapi_webhook(req: fastapi.Request) -> fastapi.Response:
                    content, status_code = await webhook_update_handler(
                        await req.json()
                    )
                    return fastapi.Response(content=content, status_code=status_code)
            case _:
                raise ValueError(
                    f"The `server` must be one of {utils.ServerType.protocols_names()}"
                )

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
        full_url = f"{callback_url.rstrip('/')}/{self._webhook_endpoint.lstrip('/')}"
        try:
            app_access_token = self.api.get_app_access_token(
                app_id=app_id, app_secret=app_secret
            )
            # noinspection PyProtectedMember
            if not self.api.set_app_callback_url(
                app_id=app_id,
                app_access_token=app_access_token["access_token"],
                callback_url=full_url,
                verify_token=verify_token,
                fields=tuple(fields or Handler._fields_to_subclasses().keys()),
            )["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info("Callback URL '%s' registered successfully", full_url)
        except WhatsAppError as e:
            raise RuntimeError(f"Failed to register callback URL '{full_url}'") from e

    async def _call_handlers(self: "WhatsApp", update: dict) -> None:
        """Call the handlers for the given update."""
        try:
            handler_type = self._get_handler(update=update)
            if handler_type is None:
                _logger.debug(
                    "Webhook ('%s') received an update but no handler was found.",
                    self._webhook_endpoint,
                )
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
        ):  # this endpoint got non-expected data
            _logger.exception(
                "Webhook ('%s') received an invalid update: %s",
                self._webhook_endpoint,
                update,
            )
            return

        if handler_type is not None:
            try:
                # noinspection PyCallingNonCallable, PyProtectedMember
                constructed_update = self._handlers_to_update_constractor[handler_type](
                    self, update
                )
                for handler in self._handlers[handler_type]:
                    try:
                        await handler.handle(self, constructed_update)
                    except Exception as e:
                        if isinstance(e, StopHandling):
                            break
                        _logger.exception(
                            "An error occurred while %s was handling an update",
                            handler.callback.__name__,
                        )
            except Exception:
                _logger.exception("Failed to construct update: %s", update)

        for raw_update_handler in self._handlers[RawUpdateHandler]:
            try:
                await raw_update_handler.handle(self, update)
            except Exception as e:
                if isinstance(e, StopHandling):
                    break
                _logger.exception(
                    "An error occurred while %s was handling an raw update",
                    raw_update_handler.callback.__name__,
                )

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
        RawUpdateHandler: lambda _, data: data,
    }
    """A dictionary that maps handler types to their respective update constructors."""

    def _get_handler(self: "WhatsApp", update: dict) -> type[Handler] | None:
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
        ) and not utils.is_installed("cryptography"):
            raise ValueError(
                "The default decryptor/encryptor requires the `cryptography` package to be installed."
                '\n>> Install it with `pip install cryptography` / pip install "pywa[cryptography]"` or use a '
                "custom decryptor/encryptor."
            )
        if endpoint == self._webhook_endpoint:
            raise ValueError(
                "The flow endpoint cannot be the same as the webhook endpoint."
            )

        async def flow_request_handler(payload: dict) -> tuple[str, int]:
            """Called by the server when a flow request is received. Returns response and status code."""
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
                    "Flow Endpoint ('%s'): Decryption failed for payload: %s",
                    endpoint,
                    payload,
                )
                return "Decryption failed", FlowRequestCannotBeDecrypted.status_code
            _logger.debug(
                "Flow Endpoint ('%s'): Received decrypted request: %s",
                endpoint,
                decrypted_request,
            )
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
                    "Flow Endpoint ('%s'): Failed to construct FlowRequest from decrypted data: %s",
                    endpoint,
                    decrypted_request,
                )

                return "Failed to construct FlowRequest", 500
            try:
                response = (
                    await callback(self, request)
                    if asyncio.iscoroutinefunction(callback)
                    else callback(self, request)
                )
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
                    "Flow Endpoint ('%s'): An error occurred while %s was handling a flow request",
                    endpoint,
                    callback.__name__,
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
                    f"Flow endpoint '({endpoint})' callback must return a `FlowResponse` or `dict`, not {type(response)}"
                )
            return response_encryptor(
                response.to_dict() if isinstance(response, FlowResponse) else response,
                aes_key,
                iv,
            ), 200

        match self._server_type:
            case utils.ServerType.FLASK:
                import flask

                if utils.is_installed("asgiref"):

                    @self._server.route(endpoint, methods=["POST"])
                    @utils.rename_func(f"({endpoint})")
                    async def flask_flow() -> tuple[str, int]:
                        return await flow_request_handler(flask.request.json)
                else:

                    @self._server.route(endpoint, methods=["POST"])
                    @utils.rename_func(f"({endpoint})")
                    def flask_flow() -> tuple[str, int]:
                        return self._loop.run_until_complete(
                            flow_request_handler(flask.request.json)
                        )
            case utils.ServerType.FASTAPI:
                import fastapi

                @self._server.post(endpoint)
                @utils.rename_func(f"({endpoint})")
                async def fastapi_flow(req: fastapi.Request) -> fastapi.Response:
                    response, status_code = await flow_request_handler(await req.json())
                    return fastapi.Response(
                        content=response,
                        status_code=status_code,
                    )
