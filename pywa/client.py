"""The WhatsApp client."""

__all__ = ("WhatsApp",)

import hashlib
import mimetypes
import os
import requests
from typing import Callable, Any, Iterable, BinaryIO
from pywa.api import WhatsAppCloudApi
from pywa.handlers import Handler, MessageHandler, ButtonCallbackHandler, SelectionCallbackHandler, RawUpdateHandler, \
    MessageStatusHandler
from pywa.types import InlineButton, SectionList, Message, CallbackButton, CallbackSelection, MessageStatus, Contact, \
    MediaUrlResponse
from pywa.webhook import Webhook


class WhatsApp:
    def __init__(
            self,
            phone_id: str | int,
            token: str,
            base_url: str = "https://graph.facebook.com",
            api_version: float | int = 17.0,
            session: requests.Session | None = None,
            server: Any | None = None,
            webhook_endpoint: str = "/",
            verify_token: str | None = None,
            filter_updates: bool = True,
    ) -> None:
        """
        Initialize the WhatsApp client.

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(phone_id="100944",token="EAADKQl9oJxx")

        Args:
            phone_id: The 'Phone number ID'
            token: The token of the WhatsApp account.
            base_url: The base URL of the WhatsApp API. Default: ``https://graph.facebook.com``
            api_version: The API version of the WhatsApp API. Default: ``17.0``
            session: The session to use for requests. (Do not use the same session for multiple WhatsApp clients!)
            server: The Flask or FastAPI app instance.
            webhook_endpoint: The endpoint to listen for incoming messages (default: ``/``).
            verify_token: The verify token of the registered webhook.
            filter_updates: Whether to filter out updates that not sended to this phone number.
        """
        self.phone_id = str(phone_id)
        self.api = WhatsAppCloudApi(
            phone_id=phone_id,
            token=token,
            session=session or requests.Session(),
            base_url=base_url,
            api_version=float(api_version),
        )
        if server is not None:
            if verify_token is None:
                raise ValueError("When listening for incoming messages, a verify token must be provided.")
            self.webhook = Webhook(
                wa_client=self,
                server=server,
                verify_token=verify_token,
                webhook_endpoint=webhook_endpoint,
                filter_updates=filter_updates,
            )
        else:
            self.webhook = None

    def add_handler(self, handler: Handler):
        if self.webhook is None:
            raise ValueError("You must initialize the WhatsApp client with an web server"
                             " (Flask or FastAPI) in order to handle incoming messages.")
        self.webhook.handlers[handler.__handler_type__].append(handler)

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
            self.add_handler(RawUpdateHandler(func, *filters))
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
            self.add_handler(MessageHandler(func, *filters))
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
            self.add_handler(ButtonCallbackHandler(func, *filters))
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
            self.add_handler(SelectionCallbackHandler(func, *filters))
            return func
        return decorator

    def on_message_status(self, *filters: Callable[["WhatsApp", MessageStatus], bool]):
        """
        Decorator to register a function as a handler for incoming message status changes.

        **DO NOT USE THIS HANDLER TO SEND MESSAGES, IT WILL CAUSE AN INFINITE LOOP!**

        Example:

            >>> @wa.on_message_status(MessageStatusFilter.READ)
            ... def delivered_handler(wa: WhatsApp, status: MessageStatus):
            ...     print(f"Message {status.id} was read by {status.from_user.wa_id}")

            >>> @wa.on_message_status(MessageStatusFilter.FAILED)
            ... def delivered_handler(wa: WhatsApp, status: MessageStatus):
            ...     print(f"Message {status.id} failed to send to {status.to_user.wa_id}. error: {status.error.message}


        Args:
            filters: Filters to apply to the incoming message status changes (filters are function that take the
                WhatsApp client and the incoming message status change and return a boolean).
        """
        def decorator(func: Callable[["WhatsApp", MessageStatus], Any]):
            self.add_handler(MessageStatusHandler(func, *filters))
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
            )['messages'][0]['id']
        return self.api.send_interactive_message(
            to=to,
            keyboard=keyboard,
            header={
                "type": "text",
                "text": header,
            } if header else None,
            body=text,
            footer=footer,
        )['messages'][0]['id']

    send_text = send_message  # alias

    def _resolve_media_param(
            self,
            media: str | bytes | BinaryIO,
            mime_type: str,
            file_name: str,
    ) -> tuple[bool, str]:
        """
        Internal method to resolve media parameters to a media ID or URL.
        """
        if isinstance(media, str):
            if media.startswith(("https://", "http://")):
                return True, media
            elif not os.path.isfile(media) and media.isdigit():
                return False, media  # assume it's a media ID
            else:
                return False, self.upload_media(
                    media=media,
                    mime_type=mimetypes.guess_type(media)[0] or mime_type,
                    file_name=os.path.basename(media) or file_name
                )
        else:
            return False, self.api.upload_media(media=media, mime_type=mime_type, file_name=file_name)['id']

    def send_image(
            self,
            to: str,
            image: str | bytes | BinaryIO,
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
            image: The image to send (either a media ID, URL, file path, bytes, or a open file object).
            caption: The caption of the image (optional, markdown allowed).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            buttons: The buttons to send with the image (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

        Returns:
            The message ID of the sent image.
        """
        is_url, image = self._resolve_media_param(media=image, mime_type="image/jpeg", file_name="image.jpg")
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=image,
                media_type="image",
                caption=caption,
            )['messages'][0]['id']
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending an image with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "image",
                "image": {
                    "link" if is_url else "id": image,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )['messages'][0]['id']

    def send_video(
            self,
            to: str,
            video: str | bytes | BinaryIO,
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
            video: The video to send (either a media ID, URL, file path, bytes, or a open file object).
            caption: The caption of the video (optional, markdown allowed).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            buttons: The buttons to send with the video (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

        Returns:
            The message ID of the sent message.
        """
        is_url, video = self._resolve_media_param(media=video, mime_type="video/mp4", file_name="video.mp4")
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=video,
                media_type="video",
                caption=caption,
            )['messages'][0]['id']
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending a video with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "video",
                "video": {
                    "link" if is_url else "id": video,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )['messages'][0]['id']

    def send_document(
            self,
            to: str,
            document: str | bytes | BinaryIO,
            file_name: str | None = None,
            caption: str | None = None,
            reply_to_message_id: str | None = None,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Send a document to a WhatsApp user.

        Example:

            >>> wa.send_document(
            ...     to="1234567890",
            ...     document="https://example.com/example_123.pdf",
            ...     file_name="example.pdf",
            ...     caption="Example PDF"
            ... )


        Args:
            to: The phone ID of the WhatsApp user.
            document: The document to send (either a media ID, URL, file path, bytes, or a open file object).
            file_name: The filename of the document (optional, The extension of the filename will specify what format the document is displayed as in WhatsApp).
            caption: The caption of the document (optional).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            buttons: The buttons to send with the document (optional).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).

        Returns:
            The message ID of the sent message.
        """
        is_url, document = self._resolve_media_param(media=document, mime_type="text/plain",
                                                     file_name=file_name or "file.text")
        if not buttons:
            return self.api.send_media(
                to=to,
                media_id_or_url=document,
                media_type="document",
                file_name=file_name,
                caption=caption,
            )['messages'][0]['id']
        if not body and not caption:
            raise ValueError("Either body or caption must be provided when sending a document with buttons.")
        return self.api.send_interactive_message(
            to=to,
            keyboard=buttons,
            header={
                "type": "document",
                "document": {
                    "link" if is_url else "id": document,
                    "filename": file_name,
                }
            },
            body=body or caption,
            footer=footer,
            reply_to_message_id=reply_to_message_id,
        )['messages'][0]['id']

    def send_audio(
            self,
            to: str,
            audio: str | bytes | BinaryIO,
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
            audio: The audio file to send (either a media ID, URL, file path, bytes, or a open file object).

        Returns:
            The message ID of the sent message.
        """
        _, audio = self._resolve_media_param(media=audio, mime_type="audio/mpeg", file_name="audio.mp3")
        return self.api.send_media(
            to=to,
            media_id_or_url=audio,
            media_type="audio",
        )['messages'][0]['id']

    def send_sticker(
            self,
            to: str,
            sticker: str | bytes | BinaryIO,
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
            sticker: The sticker to send (either a media ID, URL, file path, bytes, or an open file object).

        Returns:
            The message ID of the sent message.
        """
        _, sticker = self._resolve_media_param(media=sticker, mime_type="image/webp", file_name="sticker.webp")
        return self.api.send_media(
            to=to,
            media_id_or_url=sticker,
            media_type="sticker",
        )['messages'][0]['id']

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
        )['messages'][0]['id']

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
        )['messages'][0]['id']

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
        )['messages'][0]['id']

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
        )['messages'][0]['id']

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
        return self.api.mark_message_as_read(message_id=message_id)['success']

    def upload_media(
            self,
            media: str | bytes | BinaryIO,
            mime_type: str,
            file_name: str | None = None,
    ) -> str:
        """
        Upload media to WhatsApp servers.

        Example:
            >>> wa.upload_media(
            ...     media='https://example.com/image.jpg',
            ...     mime_type='image/jpeg',
            ... )

        Args:
            media: The media to upload (can be a URL, bytes, or a file path).
            mime_type: The MIME type of the media (required if media is bytes or a file path).
            file_name: The file name of the media (optional).

        Returns:
            The media ID.
        """
        if isinstance(media, str):
            if os.path.isfile(media):
                file, file_name, mime_type = \
                    open(media, 'rb'), os.path.basename(media), (mimetypes.guess_type(media)[0] or mime_type)
            elif media.startswith(("https://", "http://")):
                res = requests.get(media)
                res.raise_for_status()
                file, file_name, mime_type = \
                    res.content, os.path.basename(media) or file_name, (res.headers['Content-Type'] or mime_type)
            else:
                raise ValueError(f'File not found or invalid URL: {media}')
        else:
            file = media
        return self.api.upload_media(
            file_name=file_name or 'file',
            media=file,
            mime_type=mime_type,
        )['id']

    def get_media_url(
            self,
            media_id: str
    ) -> MediaUrlResponse:
        """
        Get the URL of a media.
            - The URL is valid for 5 minutes.
            - The media can be downloaded using the ``download`` method.

        Example:
            >>> wa.get_media_url(
            ...

        Args:
            media_id: The media ID.

        Returns:
            A MediaResponse object with the media URL.
        """
        res = self.api.get_media_url(media_id=media_id)
        return MediaUrlResponse(
            _client=self,
            id=res['id'],
            url=res['url'],
            mime_type=res['mime_type'],
            sha256=res['sha256'],
            file_size=res['file_size'],
        )

    def download_media(
            self,
            url: str,
            path: str | None = None,
            file_name: str | None = None,
            in_memory: bool = False,
    ) -> str | bytes:
        """
        Download a media file from WhatsApp servers.

        Args:
            url: The URL of the media file (from ``get_media_url``).
            path: The path where to save the file (if not provided, the current working directory will be used).
            file_name: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        content, mimetype = self.api.get_media_bytes(media_url=url)
        if in_memory:
            return content
        if path is None:
            path = os.getcwd()
        if file_name is None:
            file_name = hashlib.sha256(url.encode()).hexdigest() + \
                        mimetypes.guess_extension(mimetype) or '.bin'
        path = os.path.join(path, file_name)
        with open(path, "wb") as f:
            f.write(content)
        return path
