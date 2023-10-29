from __future__ import annotations

"""This module contains the Webhook class, which is used to set up a webhook for receiving incoming messages."""

__all__ = ["Webhook"]

import collections
import logging
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, Iterable

from pywa import utils
from pywa.errors import WhatsAppError
from pywa.handlers import Handler  # noqa
from pywa.handlers import (
    CallbackButtonHandler,
    CallbackSelectionHandler,
    MessageHandler,
    MessageStatusHandler,
    RawUpdateHandler,
)
from pywa.types import MessageType
from pywa.types.base_update import BaseUpdate, StopHandling  # noqa
from pywa.utils import FastAPI, Flask

if TYPE_CHECKING:
    from pywa.client import WhatsApp

_VERIFY_TIMEOUT_SEC = 6

_logger = logging.getLogger(__name__)


class Webhook:
    """This class is used by the :class:`WhatsApp` client to set up a webhook for receiving incoming messages."""

    def __init__(
        self: WhatsApp,
        server: Flask | FastAPI | None = None,
        webhook_endpoint: str = "/",
        callback_url: str | None = None,
        fields: Iterable[str] | None = None,
        app_id: int | None = None,
        app_secret: str | None = None,
        verify_token: str | None = None,
        verify_timeout: int | None = None,
    ):
        if server is not None:
            if not verify_token:
                raise ValueError(
                    "When listening for incoming updates, a verify token must be provided.\n>> The verify token can "
                    "be any string. It is used to challenge the webhook endpoint to verify that the endpoint is valid."
                )
            self._handlers: dict[
                type[Handler] | None,
                list[Callable[[WhatsApp, BaseUpdate | dict], Any]],
            ] = collections.defaultdict(list)

            hub_vt = "hub.verify_token"
            hub_ch = "hub.challenge"

            if utils.is_flask_app(server):
                import flask

                @server.route(webhook_endpoint, methods=["GET"])
                def challenge():
                    if flask.request.args.get(hub_vt) == verify_token:
                        return flask.request.args.get(hub_ch), 200
                    return "Error, invalid verification token", 403

                @server.route(webhook_endpoint, methods=["POST"])
                def webhook():
                    threading.Thread(
                        target=self._call_handlers,
                        args=(flask.request.json,),
                    ).start()
                    return "ok", 200

            elif utils.is_fastapi_app(server):
                import fastapi

                @server.get(webhook_endpoint)
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

                @server.post(webhook_endpoint)
                def webhook(payload: dict = fastapi.Body(...)):
                    threading.Thread(
                        target=self._call_handlers, args=(payload,)
                    ).start()
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
                def register_callback_url():
                    if (
                        verify_timeout is not None
                        and verify_timeout > _VERIFY_TIMEOUT_SEC
                    ):
                        time.sleep(verify_timeout - _VERIFY_TIMEOUT_SEC)
                    try:
                        app_access_token = self.api.get_app_access_token(
                            app_id=app_id, app_secret=app_secret
                        )
                        if not self.api.set_callback_url(
                            app_id=app_id,
                            app_access_token=app_access_token["access_token"],
                            callback_url=f"{callback_url}/{webhook_endpoint}",
                            verify_token=verify_token,
                            fields=tuple(
                                fields or Handler.__fields_to_subclasses__().keys()
                            ),
                        )["success"]:
                            raise ValueError("Failed to register callback URL.")
                    except WhatsAppError as e:
                        raise ValueError(f"Failed to register callback URL. Error: {e}")

                threading.Thread(target=register_callback_url).start()

    def _call_handlers(self: WhatsApp, update: dict) -> None:
        """Call the handlers for the given update."""
        handler = self._get_handler(update=update)
        for callback in self._handlers[handler]:
            try:
                # noinspection PyCallingNonCallable
                callback(self, handler.__update_constructor__(self, update))  # __call__
            except Exception as e:
                if isinstance(e, StopHandling):
                    break
                _logger.exception(e)
        for raw_update_callback in self._handlers[RawUpdateHandler]:
            try:
                raw_update_callback(self, update)
            except Exception as e:
                if isinstance(e, StopHandling):
                    break
                _logger.exception(e)

    def _get_handler(self: WhatsApp, update: dict) -> type[Handler] | None:
        """Get the handler for the given update."""
        field = update["entry"][0]["changes"][0]["field"]
        value = update["entry"][0]["changes"][0]["value"]

        # The `messages` field needs to be handled differently because it can be a message, button, selection, or status
        # This check must return handler or None *BEFORE* getting the handler from the dict!!
        if field == "messages":
            if not self.filter_updates or (
                value["metadata"]["phone_number_id"] == self.phone_id
            ):
                if "messages" in value:
                    match value["messages"][0]["type"]:
                        case MessageType.INTERACTIVE:
                            if (
                                _type := value["messages"][0]["interactive"]["type"]
                            ) == "button_reply":  # button
                                return CallbackButtonHandler
                            elif _type == "list_reply":  # selection
                                return CallbackSelectionHandler
                            _logger.warning(
                                "PyWa Webhook: Unknown interactive message type: %s"
                                % _type
                            )
                        case MessageType.BUTTON:  # button (quick reply from template)
                            return CallbackButtonHandler
                        case _:  # message
                            return MessageHandler
                elif "statuses" in value:  # status
                    return MessageStatusHandler
                _logger.warning("PyWa Webhook: Unknown message type: %s" % value)
            return None

        return Handler.__fields_to_subclasses__().get(field)
