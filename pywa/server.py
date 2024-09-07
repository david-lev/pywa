"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

__all__ = ["Server"]

import logging
import threading
from typing import TYPE_CHECKING, Callable, TypedDict

from . import utils, handlers, errors
from .handlers import (
    Handler,
    ChatOpenedHandler,
    TemplateStatusHandler,
    _EncryptedFlowRequestType,
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
from .types.base_update import BaseUpdate, StopHandling, ContinueHandling  # noqa
from .types.flows import (
    FlowRequestCannotBeDecrypted,
    FlowResponseError,  # noqa
    FlowTokenNoLongerValid,
    FlowRequestActionType,
)
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


def _extract_id_from_update(update: dict) -> str | None:
    """Extract the ID from the given update."""
    try:
        return update["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
    except (KeyError, IndexError, TypeError):
        return None


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
        RawUpdateHandler: lambda _, data: data,
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
        self._updates_ids_in_process = set[str]()

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
                "(not recommended. disable `validate_updates` to suppress this warning)"
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
            # noinspection PyProtectedMember
            self._delayed_register_callback_url(
                callback_url=f"{callback_url.rstrip('/')}/{self._webhook_endpoint.lstrip('/')}",
                app_id=app_id,
                app_secret=app_secret,
                verify_token=verify_token,
                fields=tuple(webhook_fields or Handler._fields_to_subclasses().keys()),
                delay=webhook_challenge_delay,
            )

    async def webhook_challenge_handler(self, vt: str, ch: str) -> tuple[str, int]:
        """
        Handle the verification challenge from the webhook manually.

        - Use this function only if you are using a custom server (e.g. Django, aiohttp, etc.).

        Example:

            .. code-block:: python
                :emphasize-lines: 4, 7, 8, 9, 10
                :linenos:

                from aiohttp import web
                from pywa import WhatsApp, utils

                wa = WhatsApp(..., server=None)

                async def my_challenge_handler(req: web.Request) -> web.Response:
                    challenge, status_code = await wa.webhook_challenge_handler(
                        vt=req.query[utils.HUB_VT],
                        ch=req.query[utils.HUB_CH],
                    )
                    return web.Response(text=challenge, status=status_code)

                app = web.Application()
                app.add_routes([web.get("/my_webhook", my_challenge_handler)])

                if __name__ == "__main__":
                    web.run_app(app, port=...)

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

    async def webhook_update_handler(
        self, update: dict, raw_body: bytes | None = None, hmac_header: str = None
    ) -> tuple[str, int]:
        """
        Handle the incoming update from the webhook manually.

        - Use this function only if you are using a custom server (e.g. Django, aiohttp, etc.).

        Example:

                .. code-block:: python
                    :emphasize-lines: 4, 7, 8, 9, 10, 11
                    :linenos:

                    from aiohttp import web
                    from pywa import WhatsApp, utils

                    wa = WhatsApp(..., server=None)

                    async def my_webhook_handler(req: web.Request) -> web.Response:
                        res, status_code = await wa.webhook_update_handler(
                            update=await req.json(),
                            raw_body=await req.read(),
                            hmac_header=req.headers.get(utils.HUB_SIG)
                        )
                        return web.Response(text=res, status=status_code)

                    app = web.Application()
                    app.add_routes([web.post("/my_webhook", my_webhook_handler)])

                    if __name__ == "__main__":
                        web.run_app(app, port=...)

        Args:
            update: The incoming update from the webhook (dict).
            raw_body: The raw body of the request (to calculate the signature, optional).
            hmac_header: The ``X-Hub-Signature-256`` header (to validate the signature, use ``utils.HUB_SIG`` for the key).

        Returns:
            A tuple containing the response and the status code.
        """
        if self._validate_updates:
            if not hmac_header:
                _logger.debug(
                    "Webhook ('%s') received an update without a signature",
                    self._webhook_endpoint,
                )
                return "Error, missing signature", 401
            if not utils.webhook_updates_validator(
                app_secret=self._app_secret,
                request_body=raw_body,
                x_hub_signature=hmac_header,
            ):
                _logger.debug(
                    "Webhook ('%s') received an update with an invalid signature",
                    self._webhook_endpoint,
                )
                return "Error, invalid signature", 401

        update_id: str | None = None
        _logger.debug(
            "Webhook ('%s') received an update: %s",
            self._webhook_endpoint,
            update,
        )
        if self._skip_duplicate_updates and (
            update_id := _extract_id_from_update(update)
        ):
            if update_id in self._updates_ids_in_process:
                _logger.warning(
                    "Webhook ('%s') received an update with an ID that is already being processed: %s",
                    self._webhook_endpoint,
                    update_id,
                )
                return "ok", 200
            self._updates_ids_in_process.add(update_id)
        await self._call_handlers(update)
        if self._skip_duplicate_updates:
            try:
                self._updates_ids_in_process.remove(update_id)
            except KeyError:
                pass
        return "ok", 200

    def _register_routes(self: "WhatsApp") -> None:
        match self._server_type:
            case utils.ServerType.FLASK:
                if not utils.is_installed("asgiref"):  # flask[async]
                    raise ValueError(
                        "Flask with ASGI is required to handle incoming updates asynchronously. Please install "
                        """the `asgiref` package (`pip install "flask[async]"` / `pip install "asgiref"`)"""
                    )

                _logger.info("Using Flask with ASGI")
                import flask

                @self._server.route(self._webhook_endpoint, methods=["GET"])
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                async def pywa_challenge() -> tuple[str, int]:
                    """Automatically generated by pywa to handle the verification challenge."""
                    return await self.webhook_challenge_handler(
                        vt=flask.request.args.get(utils.HUB_VT),
                        ch=flask.request.args.get(utils.HUB_CH),
                    )

                @self._server.route(self._webhook_endpoint, methods=["POST"])
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                async def pywa_webhook() -> tuple[str, int]:
                    """Automatically generated by pywa to handle incoming updates."""
                    return await self.webhook_update_handler(
                        update=flask.request.json,
                        raw_body=flask.request.data,
                        hmac_header=flask.request.headers.get(utils.HUB_SIG),
                    )

            case utils.ServerType.FASTAPI:
                _logger.info("Using FastAPI")
                import fastapi

                @self._server.get(self._webhook_endpoint)
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                async def pywa_challenge(
                    vt: str = fastapi.Query(alias=utils.HUB_VT, example="xyzxyz"),
                    ch: str = fastapi.Query(alias=utils.HUB_CH, example="1858252904"),
                ) -> fastapi.Response:
                    """Automatically generated by pywa to handle the verification challenge."""
                    content, status_code = await self.webhook_challenge_handler(
                        vt=vt,
                        ch=ch,
                    )
                    return fastapi.Response(
                        content=content,
                        status_code=status_code,
                        media_type="text/plain",
                    )

                @self._server.post(self._webhook_endpoint)
                @utils.rename_func(f"('{self._webhook_endpoint}')")
                async def pywa_webhook(
                    update: dict,
                    req: fastapi.Request,
                    hmac_header: str = fastapi.Header(
                        alias=utils.HUB_SIG, example="sha256=..."
                    ),
                ) -> fastapi.Response:
                    """Automatically generated by pywa to handle incoming updates."""
                    content, status_code = await self.webhook_update_handler(
                        update=update,
                        raw_body=await req.body(),
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
                "Webhook ('%s') received an invalid update%s: %s",
                self._webhook_endpoint,
                " (Enable `validate_updates` to ignore updates with invalid data)"
                if not self._validate_updates
                else "",
                update,
                exc_info=None,
            )
            return

        if handler_type is not None:
            try:
                constructed_update = self._handlers_to_update_constractor[handler_type](
                    self, update
                )
                await self._call_callbacks(handler_type, constructed_update)
            except Exception:
                _logger.exception("Failed to construct update: %s", update)

        await self._call_callbacks(RawUpdateHandler, update)

    async def _call_callbacks(
        self: "WhatsApp",
        handler_type: type[Handler],
        constructed_update: BaseUpdate | dict,
    ) -> None:
        """Call the handler type callbacks for the given update."""
        handled = False
        for handler in self._handlers[handler_type]:
            try:
                handled = await handler.handle(self, constructed_update)
            except StopHandling:
                break
            except ContinueHandling:
                continue
            except Exception:
                _logger.exception(
                    "An error occurred while %s was handling an update",
                    handler.callback.__name__,
                )
            if handled and not self._continue_handling:
                break

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
                "increase the delay using the `verify_timeout` parameter when initializing the WhatsApp client."
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

        - Use this function only if you are using a custom server (e.g. Django, aiohttp, etc.), else use the
          :meth:`WhatsApp.on_flow_request` decorator.


        Example:

            .. code-block:: python
                :emphasize-lines: 4, 15
                :linenos:

                from aiohttp import web
                from pywa import WhatsApp, flows

                wa = WhatsApp(..., server=None, business_private_key="...", business_private_key_password="...")

                async def my_flow_callback(wa: WhatsApp, request: flows.FlowRequest) -> flows.FlowResponse:
                    ...

                flow_handler = wa.get_flow_request_handler(
                    endpoint="/flow",
                    callback=my_flow_callback,
                )

                async def my_flow_endpoint(req: web.Request) -> web.Response:
                    response, status_code = await flow_handler.handle(await req.json())
                    return web.Response(text=response, status=status_code)

                app = web.Application()
                app.add_routes([web.post("/flow", my_flow_endpoint)])

                if __name__ == "__main__":
                    web.run_app(app, port=...)


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

        callback_wrapper = self.get_flow_request_handler(
            endpoint=endpoint,
            callback=callback,
            acknowledge_errors=acknowledge_errors,
            handle_health_check=handle_health_check,
            private_key=private_key,
            private_key_password=private_key_password,
            request_decryptor=request_decryptor,
            response_encryptor=response_encryptor,
        )

        match self._server_type:
            case utils.ServerType.FLASK:
                if not utils.is_installed("asgiref"):
                    raise ValueError(
                        "Flask with ASGI is required to handle incoming updates asynchronously. Please install "
                        """the `asgiref` package (`pip install "flask[async]"` / `pip install "asgiref"`)"""
                    )

                import flask

                @self._server.route(endpoint, methods=["POST"])
                @utils.rename_func(f"({endpoint})")
                async def pywa_flow() -> tuple[str, int]:
                    return await callback_wrapper(flask.request.json)

            case utils.ServerType.FASTAPI:
                import fastapi

                @self._server.post(endpoint)
                @utils.rename_func(f"({endpoint})")
                async def pywa_flow(
                    flow_req: _EncryptedFlowRequestType,
                ) -> fastapi.Response:
                    response, status_code = await callback_wrapper(flow_req)
                    return fastapi.Response(
                        content=response,
                        status_code=status_code,
                    )

        return callback_wrapper
