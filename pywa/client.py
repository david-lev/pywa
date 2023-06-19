import collections
import requests
from typing import Callable, Any, Iterable
from pywa.api import WhatsAppCloudApi
from pywa.handlers import Handler, MessageHandler, ButtonCallbackHandler, SelectionCallbackHandler
from pywa.types import Button, SectionList, Message, CallbackButtonReply, CallbackListReply
from pywa import webhook


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
        if app is not None:
            if verify_token is None:
                raise ValueError("When listening for incoming messages, a verify token must be provided.")
            webhook.Webhook(
                wa_client=self,
                app=app,
                verify_token=verify_token,
                webhook_endpoint=webhook_endpoint,
            )
            self._handlers = collections.defaultdict(list)
        else:
            self._handlers = None

    def add_handler(self, handler: Handler):
        if self._handlers is None:
            raise ValueError("You must initialize the WhatsApp client with an app (Flask or FastAPI) to add handlers.")
        self._handlers[handler.__handler_type__].append(handler)

    def __call_handlers(self, event: Message | CallbackButtonReply | CallbackListReply):
        for handler in self._handlers[event.__class__]:  # TODO execute in parallel
            handler(self, event)

    def on_raw_update(
            self,
            filters: Iterable[Callable[["WhatsApp", dict], bool]] | Callable[["WhatsApp", dict], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", dict], Any]):
            self.add_handler(Handler(handler=func, filters=filters))
            return func
        return decorator

    def on_message(
            self,
            filters: Iterable[Callable[["WhatsApp", Message], bool]] |
            Callable[["WhatsApp", Message], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", Message], Any]):
            self.add_handler(MessageHandler(handler=func, filters=filters))
            return func
        return decorator

    def on_callback_button(
            self,
            filters: Iterable[Callable[["WhatsApp", CallbackButtonReply], bool]] |
            Callable[["WhatsApp", CallbackButtonReply], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", CallbackButtonReply], Any]):
            self.add_handler(ButtonCallbackHandler(handler=func, filters=filters))
            return func
        return decorator

    def on_callback_selection(
            self,
            filters: Iterable[Callable[["WhatsApp", CallbackListReply], bool]] |
            Callable[["WhatsApp", CallbackListReply], bool] = None
    ):
        def decorator(func: Callable[["WhatsApp", CallbackListReply], Any]):
            self.add_handler(SelectionCallbackHandler(handler=func, filters=filters))
            return func
        return decorator

    def send_message(
            self,
            to: str,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[Button] | SectionList | None = None,
            header: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send a message to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send.
            preview_url: Whether to show a preview of the URL in the message (if any).
            reply_to_message_id: The message ID to reply to (optional).
            keyboard: The keyboard to send with the message (optional).
            header: The header of the message (if keyboard is provided, optional).
            footer: The footer of the message (if keyboard is provided, optional).

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
        return self.api.send_interactive_message(
            to=to,
            keyboard=keyboard,
            header={
                "type": "text",
                "text": header,
            } if header else None,
            body=text,
            footer=footer,
        )

    def send_image(
            self,
            to: str,
            image: str | bytes,
            caption: str | None = None,
            reply_to_message_id: str | None = None,
            buttons: list[Button] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send an image to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            image: The image to send (either a URL or a file ID).
            caption: The caption of the image (optional).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the image (optional).
            body: The body of the message (if buttons are provided, optional).
            footer: The footer of the message (if buttons are provided, optional).

        Returns:
            The message ID of the sent image.
        """
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=image,
                media_type="image",
                reply_to_message_id=reply_to_message_id,
                caption=caption,
            )
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending an image with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "image",
                "image": {
                    "link" if image.startswith(("https://", "http://")) else "id": image,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )

    def send_video(
            self,
            to: str,
            video: str | bytes,
            caption: str | None = None,
            reply_to_message_id: str | None = None,
            buttons: list[Button] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send a video to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            video: The video to send (either a URL or a file ID).
            caption: The caption of the video (optional).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the video (optional).
            body: The body of the message (if buttons are provided, optional).
            footer: The footer of the message (if buttons are provided, optional).

        Returns:
            The message ID of the sent message.
        """
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=video,
                media_type="video",
                reply_to_message_id=reply_to_message_id,
                caption=caption,
            )
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending a video with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "video",
                "video": {
                    "link" if video.startswith(("https://", "http://")) else "id": video,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )

    def send_document(
            self,
            to: str,
            document: str | bytes,
            filename: str | None = None,
            caption: str | None = None,
            reply_to_message_id: str | None = None,
            buttons: list[Button] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ):
        """
        Send a document to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            document: The document to send (either a URL or a file ID).
            filename: The filename of the document (optional).
            caption: The caption of the document (optional).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the document (optional).
            body: The body of the message (if buttons are provided, optional).
            footer: The footer of the message (if buttons are provided, optional).

        Returns:
            The message ID of the sent message.
        """
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=document,
                media_type="document",
                reply_to_message_id=reply_to_message_id,
                filename=filename,
                caption=caption,
            )
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending a document with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "document",
                "document": {
                    "link" if document.startswith(("https://", "http://")) else "id": document,
                    "filename": filename,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )

    def send_audio(
            self,
            to: str,
            audio: str | bytes,
            reply_to_message_id: str | None = None,
    ) -> str:
        """
        Send an audio file to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            audio: The audio file to send (either a URL or a file ID).
            reply_to_message_id: The message ID to reply to (optional).

        Returns:
            The message ID of the sent message.
        """
        return self.api.send_media(
            to=to,
            media_id_or_url=audio,
            media_type="audio",
            reply_to_message_id=reply_to_message_id,
        )

    def send_reaction(
            self,
            to: str,
            emoji: str,
            message_id: str,
    ) -> str:
        """
        React to a message with an emoji.

        Args:
            to: The phone ID of the WhatsApp user.
            emoji: The emoji to react with.
            message_id: The message ID to react to.

        Returns:
            The message ID of the reaction.
        """
        return self.api.send_reaction(
            to=to,
            emoji=emoji,
            message_id=message_id,
        )

    def send_location(
            self,
            to: str,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ) -> str:
        """
        Send a location to a WhatsApp user.

        Args:
            to: The phone ID of the WhatsApp user.
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location (optional).
            address: The address of the location (optional).
        """
        return self.api.send_location(
            to=to,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
        )
