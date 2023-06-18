import collections
import requests
import importlib
from typing import Callable, Any, Iterable
from pywa.api import WhatsAppCloudApi
from pywa.handlers import Handler, MessageHandler, ButtonCallbackHandler, SelectionCallbackHandler
from pywa.types import Button, SectionList, Message, CallbackButtonReply, CallbackListReply
from pywa import utils


class WhatsApp:
    def __init__(
            self,
            phone_id: str | int,
            token: str,
            app: Any | None = None,
            webhook_endpoint: str = "/pywa",
            verify_token: str | None = None,
            base_url: str = "https://graph.facebook.com",
            api_version: float = 17.0,
            session: requests.Session | None = None,
    ):
        """
        Initialize the WhatsApp client.

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(phone_id="100944", token="EAADKQl9oJxx")

        Args:
            phone_id: The phone ID of the WhatsApp account.
            token: The token of the WhatsApp account.
            app: The Flask or FastAPI app.
            webhook_endpoint: The endpoint to listen for incoming messages (default: `/pywa`).
            verify_token: The verify token of the registered webhook.
            base_url: The base URL of the WhatsApp API. Default: `https://graph.facebook.com`
            api_version: The API version of the WhatsApp API. Default: 17.0
            session: The session to use for requests. Default: New session.
        """
        self.phone_id = str(phone_id)
        self.api = WhatsAppCloudApi(
            phone_id=phone_id,
            token=token,
            session=session or requests.Session(),
            base_url=base_url,
            api_version=api_version,
        )
        self._handlers = collections.defaultdict(list)
        if app is not None:
            if verify_token is None:
                raise ValueError("When listening for incoming messages, a verify token must be provided.")
            if utils.is_flask_app(app):
                flask = importlib.import_module("flask")

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
                        if flask.request.json["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] == self.phone_id:
                            print(flask.request.json)  # TODO: Handle incoming messages
                        return "ok", 200

            elif utils.is_fastapi_app(app):
                fastapi = importlib.import_module("fastapi")

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
                        if request_body["entry"][0]["changes"][0]["value"]["metadata"][
                            "phone_number_id"] == self.phone_id:
                            print(Message.from_dict(self, request_body))  # TODO: Handle incoming messages
                        return fastapi.Response(content="ok", status_code=200)
                    return await call_next(request)

            else:
                raise ValueError("The app must be a Flask or FastAPI app.")

    def add_handler(self, handler: Handler):
        self._handlers[handler.__handler_type__].append(handler)

    def __call_handlers(self, event: Message | CallbackButtonReply | CallbackListReply):
        print("Calling handlers", self._handlers)
        for handler in self._handlers[event.__class__]:  # TODO execute in parallel
            handler(self, event)

    def on_message(
            self,
            filters: Iterable[Callable[["WhatsApp", Message], bool]] | Callable[["WhatsApp", Message], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", Message], Any]):
            self.add_handler(MessageHandler(handler=func, filters=filters))

        return decorator

    def on_button_callback(
            self,
            filters: Iterable[Callable[["WhatsApp", CallbackButtonReply], bool]] | Callable[["WhatsApp", CallbackButtonReply], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", CallbackButtonReply], Any]):
            self.add_handler(ButtonCallbackHandler(handler=func, filters=filters))

        return decorator

    def on_selection_callback(
            self,
            filters: Iterable[Callable[["WhatsApp", CallbackListReply], bool]] | Callable[["WhatsApp", CallbackListReply], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", CallbackListReply], Any]):
            self.add_handler(SelectionCallbackHandler(handler=func, filters=filters))

        return decorator

    def send_message(
            self,
            to: str,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[Button] | SectionList | None = None,
    ) -> str:
        """
        Send a message to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send.
            preview_url: Whether to show a preview of the URL in the message (if any).
            reply_to_message_id: The message ID to reply to (optional).
            keyboard: The keyboard to send with the message (optional).

        Returns:
            The message ID of the sent message.
        """
        if not keyboard:
            return self.api.send_text_message(
                to=to,
                text=text,
                preview_url=preview_url,
                reply_to_message_id=reply_to_message_id,
            )

    def send_image(
            self,
            to: str,
            image: str | bytes,
            caption: str | None = None,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_video(
            self,
            to: str,
            video: str | bytes,
            caption: str | None = None,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_document(
            self,
            to: str,
            document: str | bytes,
            filename: str | None = None,
            caption: str | None = None,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_audio(
            self,
            to: str,
            audio: str | bytes,
            caption: str | None = None,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_reaction(
            self,
            to: str,
            emoji: str,
            message_id: str,
    ):
        raise NotImplementedError

    def send_location(
            self,
            to: str,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ):
        raise NotImplementedError
