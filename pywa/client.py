import collections
import requests
from typing import Callable, Any, Iterable
from pywa.api import WhatsAppCloudApi
from pywa.handlers import Handler, MessageHandler, ButtonCallbackHandler, SelectionCallbackHandler, RawUpdateHandler, \
    MessageStatusHandler
from pywa.types import InlineButton, SectionList, Message, CallbackButton, CallbackSelection, MessageStatus, Contact
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

    def on_raw_update(self, *filters: Callable[["WhatsApp", dict], bool]):
        """
        Decorator to register a function as a handler for raw updates.

        Example:

            >>> @wa.on_raw_update()
            ... def raw_update_handler(wa: WhatsApp, update: dict):
            ...     print(update)

        Args:
            filters: Filters to apply to the incoming updates (filters are function that take the WhatsApp client and
                the incoming update and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", dict], Any]):
            self.add_handler(RawUpdateHandler(handler=func, *filters))
            return func
        return decorator

    def on_message(self, *filters: Callable[["WhatsApp", Message], bool]):
        """
        Decorator to register a function as a handler for incoming messages.

        Example:
            >>> @wa.on_message(TextFilter.equals("hello", "hi")
            ... def hello_handler(wa: WhatsApp, msg: Message):
            ...     msg.react("👋")
            ...     msg.reply_text(text="Hello from PyWa!", quote=True, buttons=[InlineButton("Help", data="help")

        Args:
            filters: Filters to apply to the incoming messages (filters are function that take the WhatsApp client and
                the incoming message and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", Message], Any]):
            self.add_handler(MessageHandler(handler=func, *filters))
            return func
        return decorator

    def on_callback_button(self, *filters: Callable[["WhatsApp", CallbackButton], bool]):
        """
        Decorator to register a function as a handler for incoming callback button presses.

        Example:

            >>> @wa.on_callback_button(CallbackFilter.data_equals("help"))
            ... def help_handler(wa: WhatsApp, btn: CallbackButton):
            ...     btn.reply_text(text="What can I help you with?")

        Args:
            filters: Filters to apply to the incoming callback button presses (filters are function that take the
                WhatsApp client and the incoming callback button and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", CallbackButton], Any]):
            self.add_handler(ButtonCallbackHandler(handler=func, *filters))
            return func
        return decorator

    def on_callback_selection(self, *filters: Callable[["WhatsApp", CallbackSelection], bool]):
        """
        Decorator to register a function as a handler for incoming callback selections.

        Example:

            >>> @wa.on_callback_selection(CallbackFilter.data_startswith("id:"))
            ... def id_handler(wa: WhatsApp, sel: CallbackSelection):
            ...     sel.reply_text(text=f"Your ID is {sel.data.split(':', 1)[1]}")

        Args:
            filters: Filters to apply to the incoming callback selections (filters are function that take the
                WhatsApp client and the incoming callback selection and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", CallbackSelection], Any]):
            self.add_handler(SelectionCallbackHandler(handler=func, *filters))
            return func
        return decorator

    def on_message_status_change(self, *filters: Callable[["WhatsApp", MessageStatus], bool]):
        """
        Decorator to register a function as a handler for incoming message status changes.

        Example:

            >>> @wa.on_message_status_change(MessageStatusFilter.READ)
            ... def delivered_handler(wa: WhatsApp, status: MessageStatus):
            ...     print(f"Message {status.id} was read by {status.from_user.wa_id}")

        Args:
            filters: Filters to apply to the incoming message status changes (filters are function that take the
                WhatsApp client and the incoming message status change and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", MessageStatus], Any]):
            self.add_handler(MessageStatusHandler(handler=func, *filters))
            return func
        return decorator

    def send_message(
            self,
            to: str,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
            keyboard: list[InlineButton] | SectionList | None = None,
            header: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send a message to a WhatsApp user.

        Example:

            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="Hello from PyWa! (https://github.com/david-lev/pywa)",
            ...     preview_url=True,
            ... )

        Example with keyboard buttons:

            >>> wa.send_message(
            ...     to="1234567890",
            ...     header="Hello from PyWa!",
            ...     text="What can I help you with?",
            ...     keyboard=[
            ...         InlineButton("Help", data="help"),
            ...         InlineButton("About", data="about"),
            ...     ],
            ...     footer="Powered by PyWa",
            ... )

        Example with a section list:

            >>> wa.send_message(
            ...     to="1234567890",
            ...     header="Hello from PyWa!",
            ...     text="What can I help you with?",
            ...     keyboard=SectionList(
            ...         button_title="Choose an option",
            ...         sections=[
            ...             Section(
            ...                 title="Help",
            ...                 rows=[
            ...                     SectionRow(
            ...                         title="Help",
            ...                         callback_data="help",
            ...                         description="Get help with PyWa",
            ...                     ),
            ...                     SectionRow(
            ...                         title="About",
            ...                         callback_data="about",
            ...                         description="Learn more about PyWa",
            ...                     ),
            ...                 ],
            ...             ),
            ...            Section(
            ...                 title="Other",
            ...                 rows=[
            ...                     SectionRow(
            ...                         title="GitHub",
            ...                         callback_data="github",
            ...                         description="View the PyWa GitHub repository",
            ...                     ),
            ...                 ],
            ...             ),
            ...         ],
            ...     ),
            ...     footer="Powered by PyWa",
            ... )


        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send (markdown allowed, max 4096 characters).
            preview_url: Whether to show a preview of the URL in the message (if any).
            reply_to_message_id: The message ID to reply to (optional).
            keyboard: The keyboard to send with the message (optional).
            header: The header of the message (if keyboard is provided, optional, up to 60 characters, no markdown allowed).
            footer: The footer of the message (if keyboard is provided, optional, up to 60 characters, markdown has no effect).

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
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send an image to a WhatsApp user.

        Example:

            >>> wa.send_image(
            ...     to="1234567890",
            ...     image="https://example.com/image.png",
            ...     caption="This is an image!",
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            image: The image to send (either a URL or a file ID).
            caption: The caption of the image (optional, markdown allowed).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the image (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

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
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send a video to a WhatsApp user.

        Example:

            >>> wa.send_video(
            ...     to="1234567890",
            ...     video="https://example.com/video.mp4",
            ...     caption="This is a video",
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            video: The video to send (either a URL or a file ID).
            caption: The caption of the video (optional, markdown allowed).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the video (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

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
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ):
        """
        Send a document to a WhatsApp user.

        Example:

            >>> wa.send_document(
            ...     to="1234567890",
            ...     document="https://example.com/example_123.pdf",
            ...     filename="Example PDF",
            ...     caption="Example PDF"
            ... )


        Args:
            to: The phone ID of the WhatsApp user.
            document: The document to send (either a URL or a file ID).
            filename: The filename of the document (optional, The extension of the filename will specify what format the document is displayed as in WhatsApp).
            caption: The caption of the document (optional).
            reply_to_message_id: The message ID to reply to (optional).
            buttons: The buttons to send with the document (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

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

        Example:

            >>> wa.send_audio(
            ...     to='1234567890',
            ...     audio='https://example.com/audio.mp3',
            ... )

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

    def send_sticker(
            self,
            to: str,
            sticker: str | bytes,
            animated: bool = False,
            reply_to_message_id: str | None = None,
    ) -> str:
        """
        Send a sticker to a WhatsApp user.
            - A static sticker needs to be 512x512 pixels and cannot exceed 100 KB.
            - An animated sticker must be 512x512 pixels and cannot exceed 500 KB.

        Example:

            >>> wa.send_sticker(
            ...     to='1234567890',
            ...     sticker='https://example.com/sticker.webp',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            sticker: The sticker to send (either a URL or a file ID).
            animated: Whether the sticker is animated (optional).
            reply_to_message_id: The message ID to reply to (optional).

        Returns:
            The message ID of the sent message.
        """
        return self.api.send_media(
            to=to,
            media_id_or_url=sticker,
            media_type="sticker",
            reply_to_message_id=reply_to_message_id,
            animated=animated,
        )

    def send_reaction(
            self,
            to: str,
            emoji: str,
            message_id: str,
    ) -> str:
        """
        React to a message with an emoji.

        Example:

            >>> wa.send_reaction(
            ...     to='1234567890',
            ...     emoji='👍',
            ...     message_id='wamid.XXX='
            ... )

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

    def remove_reaction(
            self,
            to: str,
            message_id: str,
    ) -> str:
        """
        Remove a reaction from a message.

        Example:

            >>> wa.remove_reaction(
            ...     to='1234567890',
            ...     message_id='wamid.XXX='
            ... )
        """
        return self.api.send_reaction(
            to=to,
            message_id=message_id,
            emoji=""
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

        Example:

            >>> wa.send_location(
            ...     to='1234567890',
            ...     latitude=37.4847483695049,
            ...     longitude=--122.1473373086664,
            ...     name='WhatsApp HQ',
            ...     address='Menlo Park, 1601 Willow Rd, United States',
            ... )

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

    def send_contact(
            self,
            to: str,
            contact: Contact | Iterable[Contact],
            reply_to_message_id: str | None = None,
    ) -> str:
        """
        Send a contact to a WhatsApp user.

        Example:

            >>> from pywa.types import Contact
            >>> wa.send_contact(
            ...     to='1234567890',
            ...     contact=Contact(
            ...         name=Contact.Name(formatted_name='David Lev', first_name='David'),
            ...         phones=[Contact.Phone(phone='1234567890', wa_id='1234567890', type='MOBILE')],
            ...         emails=[Contact.Email(email='test@test.com', type='WORK')],
            ...         urls=[Contact.Url(url='https://exmaple.com', type='HOME')],
            ...      )
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            contact: The contact/s to send.
            reply_to_message_id: The message ID to reply to (optional).

        Returns:
            The message ID of the sent message.
        """
        return self.api.send_contacts(
            to=to,
            contacts=contact if isinstance(contact, Iterable) else [contact],
            reply_to_message_id=reply_to_message_id,
        )

    def mark_message_as_read(
            self,
            message_id: str,
    ) -> bool:
        """
        Mark a message as read.

        Args:
            message_id: The message ID to mark as read.

        Returns:
            Whether the message was marked as read.
        """
        return self.api.mark_message_as_read(message_id=message_id)
