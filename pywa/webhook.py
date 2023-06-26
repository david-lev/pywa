from __future__ import annotations

import collections
from typing import Union, TYPE_CHECKING, Callable, Any
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus, BaseUpdate
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

        if utils.is_flask_app(server):
            import flask

            @server.before_request
            def before_request():
                if flask.request.path != webhook_endpoint:
                    return
                if flask.request.method == "GET":
                    if verify_token == flask.request.args.get("hub.verify_token"):
                        return flask.request.args.get("hub.challenge"), 200
                    else:
                        return "Error, invalid verification token", 403
                elif flask.request.method == "POST":
                    if not filter_updates or (
                            flask.request.json["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
                            == wa_client.phone_id):
                        for raw_update_handler in self.handlers["raw_update"]:
                            raw_update_handler(wa_client, flask.request.json)
                        update, key = convert_dict_to_update(client=wa_client, d=flask.request.json)
                        for handler in self.handlers[key]:  # TODO execute in parallel
                            handler(wa_client, update)
                    return "ok", 200

        elif utils.is_fastapi_app(server):
            import fastapi

            @server.middleware("http")
            async def before_request(request: fastapi.Request, call_next: Callable):
                if request.url.path != webhook_endpoint:
                    return await call_next(request)
                if request.method == "GET":
                    if verify_token == request.query_params.get("hub.verify_token"):
                        return fastapi.Response(content=request.query_params.get("hub.challenge"), status_code=200)
                    else:
                        return fastapi.Response(content="Error, invalid verification token", status_code=403)
                elif request.method == "POST":
                    request_body = await request.json()
                    if not filter_updates or (
                            request_body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
                            == wa_client.phone_id):
                        for raw_update_handler in self.handlers["raw_update"]:
                            raw_update_handler(wa_client, request_body)
                        update, key = convert_dict_to_update(client=wa_client, d=request_body)
                        handler: Callable[[WhatsApp, BaseUpdate], Any]
                        for handler in self.handlers[key]:  # TODO execute in parallel
                            handler(wa_client, update)
                    return fastapi.Response(content="ok", status_code=200)
                return await call_next(request)

        else:
            raise ValueError("The app must be a Flask or FastAPI app.")


def convert_dict_to_update(client: WhatsApp, d: dict) -> tuple[BaseUpdate, str]:
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
        return MessageStatus.from_dict(client=client, value=value), "status"
    else:
        raise ValueError("Invalid webhook data: " + str(d))
