from __future__ import annotations

"""The webhook module contains the Webhook class, which is used to register a webhook to listen for incoming 
messages."""

import logging
import collections
import threading
from typing import TYPE_CHECKING, Callable, Any, Type
from pywa.types.base_update import BaseUpdate
from pywa import utils
from pywa.handlers import (
    Handler,  # noqa
    MessageHandler, CallbackButtonHandler, CallbackSelectionHandler, RawUpdateHandler, MessageStatusHandler
)
from pywa.types import MessageType
from pywa.utils import Flask, FastAPI

if TYPE_CHECKING:
    from pywa import WhatsApp

__all__ = ["Webhook"]


class Webhook:
    """Register a webhook to listen for incoming messages."""

    def __init__(
            self,
            wa_client: WhatsApp,
            server: Flask | FastAPI,
            verify_token: str,
            webhook_endpoint: str,
            filter_updates: bool
    ):
        self.handlers: dict[Type[Handler] | None, list[Callable[[WhatsApp, BaseUpdate | dict], Any]]] \
            = collections.defaultdict(list)
        self.wa_client = wa_client
        self.server = server
        self.verify_token = verify_token
        self.webhook_endpoint = webhook_endpoint
        self.filter_updates = filter_updates

        hub_vt = "hub.verify_token"
        hub_ch = "hub.challenge"

        if utils.is_flask_app(self.server):
            import flask

            @self.server.route(self.webhook_endpoint, methods=["GET"])
            def verify_token():
                if flask.request.args.get(hub_vt) == self.verify_token:
                    return flask.request.args.get(hub_ch), 200
                return "Error, invalid verification token", 403

            @self.server.route(self.webhook_endpoint, methods=["POST"])
            def webhook():
                threading.Thread(target=self.call_handlers, args=(flask.request.json,)).start()
                return "ok", 200

        elif utils.is_fastapi_app(self.server):
            import fastapi

            @self.server.get(self.webhook_endpoint)
            def verify_token(
                    token: str = fastapi.Query(..., alias=hub_vt),
                    challenge: str = fastapi.Query(..., alias=hub_ch)
            ):
                if token == self.verify_token:
                    return fastapi.Response(content=challenge, status_code=200)
                return fastapi.Response(content="Error, invalid verification token", status_code=403)

            @self.server.post(self.webhook_endpoint)
            def webhook(payload: dict = fastapi.Body(...)):
                threading.Thread(target=self.call_handlers, args=(payload,)).start()
                return fastapi.Response(content="ok", status_code=200)

        else:
            raise ValueError("The server must be a Flask or FastAPI app.")

    def call_handlers(self, update: dict) -> None:
        """Call the handlers for the given update."""
        handler = self._get_handler(update=update)
        for func in self.handlers[handler]:
            # noinspection PyCallingNonCallable
            func(self.wa_client, handler.__update_constructor__(self.wa_client, update))
        for raw_update_func in self.handlers[RawUpdateHandler]:
            raw_update_func(self.wa_client, update)

    def _get_handler(self, update: dict) -> Type[Handler] | None:
        """Get the handler for the given update."""
        field = update["entry"][0]["changes"][0]["field"]
        value = update["entry"][0]["changes"][0]["value"]

        # The `messages` field needs to be handled differently because it can be a message, button, selection, or status
        if field == 'messages' and (
            not self.filter_updates or (value["metadata"]["phone_number_id"] == self.wa_client.phone_id)
        ):
            if 'messages' in value:
                match value["messages"][0]["type"]:
                    case MessageType.INTERACTIVE:
                        if (_type := value["messages"][0]["interactive"]["type"]) == "button_reply":  # button
                            return CallbackButtonHandler
                        elif _type == "list_reply":  # selection
                            return CallbackSelectionHandler
                        logging.warning("PyWa Webhook: Unknown interactive message type: %s" % _type)
                    case MessageType.BUTTON:  # button (quick reply from template)
                        return CallbackButtonHandler
                    case _:  # message
                        return MessageHandler

            elif 'statuses' in value:  # status
                return MessageStatusHandler
            else:
                logging.warning("PyWa Webhook: Unknown message type: %s" % value)
        return Handler.__fields_to_subclasses__().get(field)
