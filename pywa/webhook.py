from __future__ import annotations

"""The webhook module contains the Webhook class, which is used to register a webhook to listen for incoming 
messages."""

import collections
from typing import Union, TYPE_CHECKING, Callable, Any
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus
from pywa.types.base_update import BaseUpdate
from pywa import utils

if TYPE_CHECKING:
    from pywa import WhatsApp

__all__ = ["Webhook"]


class Webhook:
    """Register a webhook to listen for incoming messages."""

    def __init__(
            self,
            wa_client: WhatsApp,
            server: Union["flask.Flask", "fastapi.FastAPI"],
            verify_token: str,
            webhook_endpoint: str,
            filter_updates: bool
    ):
        self.handlers: dict[str, list[Callable[[WhatsApp, BaseUpdate | dict], Any]]] = collections.defaultdict(list)
        self.wa_client = wa_client
        self.server = server
        self.verify_token = verify_token
        self.webhook_endpoint = webhook_endpoint
        self.filter_updates = filter_updates

        if utils.is_flask_app(self.server):
            import flask

            @self.server.before_request
            def before_request():
                if flask.request.path != self.webhook_endpoint:
                    return
                if flask.request.method == "GET":
                    if flask.request.args.get("hub.verify_token") == self.verify_token:
                        return flask.request.args.get("hub.challenge"), 200
                    else:
                        return "Error, invalid verification token", 403
                elif flask.request.method == "POST":
                    self.call_handlers(update=flask.request.json)
                    return "ok", 200

        elif utils.is_fastapi_app(self.server):
            import fastapi

            @self.server.middleware("http")
            async def before_request(request: fastapi.Request, call_next: Callable):
                if request.url.path != self.webhook_endpoint:
                    return await call_next(request)
                if request.method == "GET":
                    if request.query_params.get("hub.verify_token") == self.verify_token:
                        return fastapi.Response(content=request.query_params.get("hub.challenge"), status_code=200)
                    else:
                        return fastapi.Response(content="Error, invalid verification token", status_code=403)
                elif request.method == "POST":
                    request_body = await request.json()
                    self.call_handlers(update=request_body)
                    return fastapi.Response(content="ok", status_code=200)
                return await call_next(request)

        else:
            raise ValueError("The app must be a Flask or FastAPI app.")

    def call_handlers(self, update: dict) -> None:
        """Call the handlers for the given update."""
        try:
            if not self.filter_updates or (
                    update["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] == self.wa_client.phone_id):
                for raw_update_handler in self.handlers["raw_update"]:
                    raw_update_handler(self.wa_client, update)
                update, key = self.convert_dict_to_update(client=self.wa_client, d=update)
                if key is None:
                    return
                for handler in self.handlers[key]:  # TODO execute in parallel
                    handler(self.wa_client, update)
        except (KeyError, IndexError):  # the update not send to this phone and filter_updates is True
            pass

    @staticmethod
    def convert_dict_to_update(client: WhatsApp, d: dict) -> tuple[BaseUpdate | None, str | None]:
        """Convert a webhook dict to a BaseUpdate object."""
        value = d["entry"][0]["changes"][0]["value"]
        if 'messages' in value:
            if value["messages"][0]["type"] != "interactive":
                return Message.from_dict(client=client, value=value), "message"
            else:
                if value["messages"][0]["interactive"]["type"] == "button_reply":
                    return CallbackButton.from_dict(client=client, value=value), "button"
                elif value["messages"][0]["interactive"]["type"] == "list_reply":
                    return CallbackSelection.from_dict(client=client, value=value), "selection"

        elif 'statuses' in value:
            return MessageStatus.from_dict(client=client, value=value), "message_status"
        return None, None  # the update is not supported

