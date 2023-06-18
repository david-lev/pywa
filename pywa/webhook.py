from typing import Union, TYPE_CHECKING, Callable
from pywa.types import Message
from pywa import utils

if TYPE_CHECKING:
    from pywa import WhatsApp


class Webhook:
    """Register a webhook to listen for incoming messages."""
    def __init__(
            self,
            wa_client: "WhatsApp",
            app: Union["flask.Flask", "fastapi.FastAPI"],
            verify_token: str,
            webhook_endpoint: str
    ):
        if utils.is_flask_app(app):
            import flask

            @app.before_request
            def before_request():
                if flask.request.path != webhook_endpoint:
                    return
                if flask.request.method == "GET":
                    if verify_token == flask.request.args.get("hub.verify_token"):
                        return flask.request.args.get("hub.challenge"), 200
                    else:
                        return "Error, invalid verification token", 403
                elif flask.request.method == "POST":
                    if flask.request.json["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] \
                            == wa_client.phone_id:
                        print(flask.request.json)  # TODO: Handle incoming messages
                    return "ok", 200

        elif utils.is_fastapi_app(app):
            import fastapi

            @app.middleware("http")
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
                    if request_body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] \
                            == wa_client.phone_id:
                        print(Message.from_dict(wa_client, request_body))  # TODO: Handle incoming messages
                    return fastapi.Response(content="ok", status_code=200)
                return await call_next(request)

        else:
            raise ValueError("The app must be a Flask or FastAPI app.")
