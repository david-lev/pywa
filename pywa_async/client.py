"""The WhatsApp Async client."""

from __future__ import annotations

__all__ = ["WhatsApp"]


from pywa.client import (
    WhatsApp,
    _DEFAULT_WORKERS,
    _MISSING,
    _resolve_buttons_param,
    _resolve_tracker_param,
    _get_interactive_msg,
    _get_media_msg,
    _get_flow_fields,
    _media_types_default_filenames,
)  # noqa MUST BE IMPORTED FIRST
from .handlers import (
    MessageHandler,
    MessageStatusHandler,
    CallbackButtonHandler,
    CallbackSelectionHandler,
    FlowCompletionHandler,
    RawUpdateHandler,
    Handler,
    TemplateStatusHandler,
    ChatOpenedHandler,
)
from pywa.types.base_update import BaseUpdate

import threading
import logging
import dataclasses
import functools
import hashlib
import json
import mimetypes
import os
import pathlib
import warnings
from typing import BinaryIO, Iterable, Literal, Callable, Awaitable, Any

import httpx

from .types import (
    TemplateStatus,
    MessageStatus,
    CallbackButton,
    CallbackSelection,
    ChatOpened,
    FlowCompletion,
)
from .errors import WhatsAppError
from . import utils
from .api import WhatsAppCloudApiAsync

from .types import (
    BusinessProfile,
    Button,
    ButtonUrl,
    CommerceSettings,
    Contact,
    Industry,
    MediaUrlResponse,
    Message,
    NewTemplate,
    ProductsSection,
    SectionList,
    Template,
    TemplateResponse,
    FlowButton,
    MessageType,
    FlowStatus,
    BusinessPhoneNumber,
    Command,
    CallbackData,
)
from .types.callback import CallbackDataT
from .types.flows import (
    FlowCategory,
    FlowJSON,
    FlowDetails,
    FlowValidationError,
    FlowAsset,
)
from .types.others import InteractiveType
from .utils import FastAPI, Flask

_logger = logging.getLogger(__name__)


class WhatsApp(WhatsApp):
    def __init__(
        self,
        phone_id: str | int,
        token: str,
        *,
        session: httpx.AsyncClient | None = None,
        server: Flask | FastAPI | None = None,
        webhook_endpoint: str = "/",
        verify_token: str | None = None,
        filter_updates: bool = True,
        business_account_id: str | int | None = None,
        callback_url: str | None = None,
        fields: Iterable[str] | None = None,
        app_id: int | None = None,
        app_secret: str | None = None,
        verify_timeout: int | None = None,
        business_private_key: str | None = None,
        business_private_key_password: str | None = None,
        flows_request_decryptor: utils.FlowRequestDecryptor
        | None = utils.default_flow_request_decryptor,
        flows_response_encryptor: utils.FlowResponseEncryptor
        | None = utils.default_flow_response_encryptor,
        max_workers: int = _DEFAULT_WORKERS,
        base_url: str = "https://graph.facebook.com",
        api_version: str
        | int
        | float
        | Literal[utils.Version.GRAPH_API] = utils.Version.GRAPH_API,
    ) -> None:
        """
        The Async WhatsApp client.
            - Full documentation on `pywa.readthedocs.io <https://pywa.readthedocs.io>`_.

        Example without webhook:

            >>> from pywa_async import WhatsApp
            >>> wa = WhatsApp(phone_id="100944",token="EAADKQl9oJxx")

        Example with webhook (using Flask):

            >>> from pywa_async import WhatsApp
            >>> from flask import Flask
            >>> flask_app = Flask(__name__)
            >>> wa = WhatsApp(
            ...     phone_id="100944",
            ...     token="EAADKQl9oJxx",
            ...     server=flask_app,
            ...     callback_url='https://6b3e.ngrok.io',
            ...     verify_token="XYZ123",
            ...     app_id=1234567890,
            ...     app_secret="my_app_secret",
            ... )
            >>> @wa.on_message()
            ... async def message_handler(_: WhatsApp, msg: Message): await msg.reply("Hello!")
            >>> flask_app.run(port=8000)

        Args:
            phone_id: The Phone number ID (Not the phone number itself, the ID can be found in the App dashboard).
            token: The token of the WhatsApp business account (In production, you should
             `use permanent token <https://developers.facebook.com/docs/whatsapp/business-management-api/get-started>`_).
            base_url: The base URL of the WhatsApp API (Do not change unless you know what you're doing).
            api_version: The API version of the WhatsApp Cloud API (default to the latest version).
            session: The session to use for httpx (default: new ``httpx.AsyncClient``, For cases where you want to
             use a custom session, e.g. for proxy support. Do not use the same session across multiple WhatsApp clients!).
            server: The Flask or FastAPI app instance to use for the webhook. required when you want to handle incoming
             updates.
            callback_url: The callback URL to register (optional, only if you want pywa to register the callback URL for
             you).
            verify_token: The verify token of the registered ``callback_url`` (Required when ``server`` is provided.
             The verify token can be any string. It is used to challenge the webhook endpoint to verify that the
             endpoint is valid).
            verify_timeout: The timeout (in seconds) to wait for the verify token to be sent to the server (optional,
             for cases where the server/network is slow or the server is taking a long time to start).
            fields: The fields to register for the callback URL (optional, if not provided, all supported fields will be
             registered. modify this if you want to reduce the number of unused requests to your server).
            app_id: The ID of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
             (optional, required when registering a ``callback_url``).
            app_secret: The secret of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
             (optional, required when registering a ``callback_url``).
            webhook_endpoint: The endpoint to listen for incoming messages (if you're using the server for another purpose,
             or for multiple WhatsApp clients, you can change this to avoid conflicts).
            filter_updates: Whether to filter out user updates that are not sent to this phone_id (default: ``True``, does
             not apply to raw updates or updates that are not user-related).
            business_account_id: The WhatsApp business account ID that owns the phone ID (optional, required for some API
             methods).
            business_private_key: The global private key to use in the ``flows_request_decryptor``
            business_private_key_password: The global private key password (if needed) to use in the ``flows_request_decryptor``
            flows_request_decryptor: The global flows requests decryptor implementation to use to decrypt Flows requests.
            flows_response_encryptor: The global flows response encryptor implementation to use to encrypt Flows responses.
            max_workers: The maximum number of workers to use for handling incoming updates (optional, default: ``min(32,os.cpu_count()+4)``,
        """
        super().__init__(
            phone_id=phone_id,
            token=token,
            base_url=base_url,
            api_version=api_version,
            session=session,
            server=server,
            webhook_endpoint=webhook_endpoint,
            verify_token=verify_token,
            filter_updates=filter_updates,
            business_account_id=business_account_id,
            callback_url=callback_url,
            fields=fields,
            app_id=app_id,
            app_secret=app_secret,
            verify_timeout=verify_timeout,
            business_private_key=business_private_key,
            business_private_key_password=business_private_key_password,
            flows_request_decryptor=flows_request_decryptor,
            flows_response_encryptor=flows_response_encryptor,
            max_workers=max_workers,
        )

    def __str__(self):
        return f"WhatsAppAsync(phone_id={self.phone_id!r})"

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

    def _setup_api(
        self,
        session: httpx.AsyncClient | None,
        token: str,
        base_url: str,
        api_version: float,
    ) -> None:
        self.api = WhatsAppCloudApiAsync(
            phone_id=self.phone_id,
            token=token,
            session=session or httpx.AsyncClient(),
            base_url=base_url,
            api_version=api_version,
        )

    def _delayed_register_callback_url(
        self,
        callback_url: str,
        app_id: int,
        app_secret: str,
        verify_token: str,
        fields: tuple[str, ...] | None,
        delay: int,
    ) -> None:
        threading.Timer(
            delay,
            function=lambda: self._loop.create_task(
                self._register_callback_url(
                    callback_url=callback_url,
                    app_id=app_id,
                    app_secret=app_secret,
                    verify_token=verify_token,
                    fields=fields,
                )
            ),
        ).start()

    async def _register_callback_url(
        self,
        callback_url: str,
        app_id: int,
        app_secret: str,
        verify_token: str,
        fields: tuple[str, ...] | None,
    ) -> None:
        try:
            app_access_token = await self.api.get_app_access_token(
                app_id=app_id, app_secret=app_secret
            )
            res = await self.api.set_app_callback_url(
                app_id=app_id,
                app_access_token=app_access_token["access_token"],
                callback_url=callback_url,
                verify_token=verify_token,
                fields=fields,
            )
            if not res["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info("Callback URL '%s' registered successfully", callback_url)
        except WhatsAppError as e:
            raise RuntimeError(
                f"Failed to register callback URL '{callback_url}'"
            ) from e

    async def send_message(
        self,
        to: str | int,
        text: str,
        header: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | SectionList | FlowButton | None = None,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a message to a WhatsApp user.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="Hello from PyWa! (https://github.com/david-lev/pywa)",
            ...     preview_url=True,
            ... )

        Example with keyboard buttons:

            >>> from pywa_async.types import Button
            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="What can I help you with?",
            ...     footer="Powered by PyWa",
            ...     buttons=[
            ...         Button("Help", data="help"),
            ...         Button("About", data="about"),
            ...     ],
            ... )

        Example with a button url:

            >>> from pywa_async.types import ButtonUrl
            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="Hello from PyWa!",
            ...     footer="Powered by PyWa",
            ...     buttons=ButtonUrl(
            ...         title="PyWa GitHub",
            ...         url="https://github.com/david-lev/pywa",
            ...     )
            ... )

        Example with a section list:

            >>> from pywa_async.types import SectionList, Section, SectionRow
            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="What can I help you with?",
            ...     footer="Powered by PyWa",
            ...     buttons=SectionList(
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
            ... )

        Example with a flow button:

            >>> from pywa_async.types import FlowButton, FlowActionType
            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="We love to get feedback!",
            ...     footer="Powered by PyWa",
            ...     buttons=FlowButton(
            ...         title="Feedback",
            ...         flow_id="1234567890",
            ...         flow_token="AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
            ...         flow_action_type=FlowActionType.NAVIGATE,
            ...         flow_action_screen="RECOMMENDED"
            ...     ),
            ... )


        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send (`markdown <https://faq.whatsapp.com/539178204879377>`_ allowed, max 4096 characters).
            header: The header of the message (if ``buttons`` are provided, optional, up to 60 characters,
             no `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if ``buttons`` are provided, optional, up to 60 characters,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the message (optional).
            preview_url: Whether to show a preview of the URL in the message (if any).
            reply_to_message_id: The message ID to reply to (optional).
            keyboard: Deprecated and will be removed in a future version, use ``buttons`` instead.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        if keyboard is not None:
            buttons = keyboard
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                message="send_message | reply_text: "
                "`keyboard` is deprecated and will be removed in a future version, use `buttons` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        if not buttons:
            return (
                await self.api.send_message(
                    to=str(to),
                    typ=MessageType.TEXT,
                    msg={"body": text, "preview_url": preview_url},
                    reply_to_message_id=reply_to_message_id,
                    biz_opaque_callback_data=_resolve_tracker_param(tracker),
                )
            )["messages"][0]["id"]
        typ, kb = _resolve_buttons_param(buttons)
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=typ,
                    action=kb,
                    header={
                        "type": MessageType.TEXT,
                        "text": header,
                    }
                    if header
                    else None,
                    body=text,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    send_text = send_message  # alias

    async def send_image(
        self,
        to: str | int,
        image: str | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        body: None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | FlowButton | None = None,
        reply_to_message_id: str | None = None,
        mime_type: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send an image to a WhatsApp user.
            - Images must be 8-bit, RGB or RGBA.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_image(
            ...     to="1234567890",
            ...     image="https://example.com/image.png",
            ...     caption="This is an image!",
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            image: The image to send (either a media ID, URL, file path, bytes, or an open file object. When buttons are
             provided, only URL is supported).
            caption: The caption of the image (required when buttons are provided,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the image (optional).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            mime_type: The mime type of the image (optional, required when sending an image as bytes or a file object,
             or file path that does not have an extension).
            body: Deprecated and will be removed in a future version, use ``caption`` instead.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent image message.
        """

        if body is not None:
            caption = body
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                message="send_image | reply_image: "
                "`body` is deprecated and will be removed in a future version, use `caption` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        is_url, image = await _resolve_media_param(
            wa=self,
            media=image,
            mime_type=mime_type,
            media_type=MessageType.IMAGE,
            filename=None,
        )
        if not buttons:
            return (
                await self.api.send_message(
                    to=str(to),
                    typ=MessageType.IMAGE,
                    msg=_get_media_msg(
                        media_id_or_url=image,
                        is_url=is_url,
                        caption=caption,
                    ),
                    biz_opaque_callback_data=_resolve_tracker_param(tracker),
                )
            )["messages"][0]["id"]
        if not caption:
            raise ValueError(
                "A caption must be provided when sending an image with buttons."
            )
        typ, kb = _resolve_buttons_param(buttons)
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=typ,
                    action=kb,
                    header={
                        "type": MessageType.IMAGE,
                        "image": {
                            "link" if is_url else "id": image,
                        },
                    },
                    body=caption,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_video(
        self,
        to: str | int,
        video: str | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        body: None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | FlowButton | None = None,
        reply_to_message_id: str | None = None,
        mime_type: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a video to a WhatsApp user.
            - Only H.264 video codec and AAC audio codec is supported.
            - Videos with a single audio stream or no audio stream are supported.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_video(
            ...     to="1234567890",
            ...     video="https://example.com/video.mp4",
            ...     caption="This is a video",
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            video: The video to send (either a media ID, URL, file path, bytes, or an open file object. When buttons are
             provided, only URL is supported).
            caption: The caption of the video (required when sending a video with buttons,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the video (optional).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            mime_type: The mime type of the video (optional, required when sending a video as bytes or a file object,
             or file path that does not have an extension).
            body: Deprecated and will be removed in a future version, use ``caption`` instead.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent video.
        """

        if body is not None:
            caption = body
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                message="send_video | reply_video: "
                "`body` is deprecated and will be removed in a future version, use `caption` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        is_url, video = await _resolve_media_param(
            wa=self,
            media=video,
            mime_type=mime_type,
            media_type=MessageType.VIDEO,
            filename=None,
        )
        if not buttons:
            return (
                await self.api.send_message(
                    to=str(to),
                    typ=MessageType.VIDEO,
                    msg=_get_media_msg(
                        media_id_or_url=video,
                        is_url=is_url,
                        caption=caption,
                    ),
                    biz_opaque_callback_data=_resolve_tracker_param(tracker),
                )
            )["messages"][0]["id"]
        if not caption:
            raise ValueError(
                "A caption must be provided when sending a video with buttons."
            )
        typ, kb = _resolve_buttons_param(buttons)
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=typ,
                    action=kb,
                    header={
                        "type": MessageType.VIDEO,
                        "video": {
                            "link" if is_url else "id": video,
                        },
                    },
                    body=caption,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_document(
        self,
        to: str | int,
        document: str | pathlib.Path | bytes | BinaryIO,
        filename: str | None = None,
        caption: str | None = None,
        body: None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | FlowButton | None = None,
        reply_to_message_id: str | None = None,
        mime_type: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a document to a WhatsApp user.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_document(
            ...     to="1234567890",
            ...     document="https://example.com/example_123.pdf",
            ...     filename="example.pdf",
            ...     caption="Example PDF"
            ... )


        Args:
            to: The phone ID of the WhatsApp user.
            document: The document to send (either a media ID, URL, file path, bytes, or an open file object. When
             buttons are provided, only URL is supported).
            filename: The filename of the document (optional, The extension of the filename will specify what format the
             document is displayed as in WhatsApp).
            caption: The caption of the document (required when sending a document with buttons,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the document (optional).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            mime_type: The mime type of the document (optional, required when sending a document as bytes or a file
             object, or file path that does not have an extension).
            body: Deprecated and will be removed in a future version, use ``caption`` instead.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent document.
        """

        if body is not None:
            caption = body
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                message="send_document | reply_document: "
                "`body` is deprecated and will be removed in a future version, use `caption` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        is_url, document = await _resolve_media_param(
            wa=self,
            media=document,
            mime_type=mime_type,
            filename=filename,
            media_type=None,
        )
        if not buttons:
            return (
                await self.api.send_message(
                    to=str(to),
                    typ=MessageType.DOCUMENT,
                    msg=_get_media_msg(
                        media_id_or_url=document,
                        is_url=is_url,
                        caption=caption,
                        filename=filename,
                    ),
                    biz_opaque_callback_data=_resolve_tracker_param(tracker),
                )
            )["messages"][0]["id"]
        if not caption:
            raise ValueError(
                "A caption must be provided when sending a document with buttons."
            )
        type_, kb = _resolve_buttons_param(buttons)
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=type_,
                    action=kb,
                    header={
                        "type": MessageType.DOCUMENT,
                        "document": {
                            "link" if is_url else "id": document,
                            "filename": filename,
                        },
                    },
                    body=caption,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_audio(
        self,
        to: str | int,
        audio: str | pathlib.Path | bytes | BinaryIO,
        mime_type: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send an audio file to a WhatsApp user.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_audio(
            ...     to='1234567890',
            ...     audio='https://example.com/audio.mp3',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            audio: The audio file to send (either a media ID, URL, file path, bytes, or an open file object).
            mime_type: The mime type of the audio file (optional, required when sending an audio file as bytes or a file
             object, or file path that does not have an extension).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent audio file.
        """
        is_url, audio = await _resolve_media_param(
            wa=self,
            media=audio,
            mime_type=mime_type,
            media_type=MessageType.AUDIO,
            filename=None,
        )
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.AUDIO,
                msg=_get_media_msg(
                    media_id_or_url=audio,
                    is_url=is_url,
                ),
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_sticker(
        self,
        to: str | int,
        sticker: str | pathlib.Path | bytes | BinaryIO,
        mime_type: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a sticker to a WhatsApp user.
            - A static sticker needs to be 512x512 pixels and cannot exceed 100 KB.
            - An animated sticker must be 512x512 pixels and cannot exceed 500 KB.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_sticker(
            ...     to='1234567890',
            ...     sticker='https://example.com/sticker.webp',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            sticker: The sticker to send (either a media ID, URL, file path, bytes, or an open file object).
            mime_type: The mime type of the sticker (optional, required when sending a sticker as bytes or a file
             object, or file path that does not have an extension).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        is_url, sticker = await _resolve_media_param(
            wa=self,
            media=sticker,
            mime_type=mime_type,
            filename=None,
            media_type=MessageType.STICKER,
        )
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.STICKER,
                msg=_get_media_msg(
                    media_id_or_url=sticker,
                    is_url=is_url,
                ),
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_reaction(
        self,
        to: str | int,
        emoji: str,
        message_id: str,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        React to a message with an emoji.
            - You can react to incoming messages by using the
              :py:func:`~pywa.types.base_update.BaseUserUpdate.react` method on every update.

                >>> wa = WhatsApp(...)
                >>> @wa.on_message()
                ... def message_handler(_: WhatsApp, msg: Message):
                ...     msg.react('👍')

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_reaction(
            ...     to='1234567890',
            ...     emoji='👍',
            ...     message_id='wamid.XXX='
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            emoji: The emoji to react with.
            message_id: The message ID to react to.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the reaction (You can't use this message id to remove the reaction or perform any other
            action on it. instead, use the message ID of the message you reacted to).
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.REACTION,
                msg={"emoji": emoji, "message_id": message_id},
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def remove_reaction(
        self,
        to: str | int,
        message_id: str,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Remove reaction from a message.
            - You can remove reactions from incoming messages by using the
              :py:func:`~pywa.types.base_update.BaseUserUpdate.unreact` method on every update.

                >>> wa = WhatsApp(...)
                >>> @wa.on_message()
                ... def message_handler(_: WhatsApp, msg: Message):
                ...     msg.unreact()

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.remove_reaction(
            ...     to='1234567890',
            ...     message_id='wamid.XXX='
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            message_id: The message ID to remove the reaction from.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the reaction (You can't use this message id to re-react or perform any other action on it.
            instead, use the message ID of the message you unreacted to).
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.REACTION,
                msg={"emoji": "", "message_id": message_id},
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_location(
        self,
        to: str | int,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a location to a WhatsApp user.

        Example:

            >>> wa = WhatsApp(...)
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
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent location.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.LOCATION,
                msg={
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name,
                    "address": address,
                },
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def request_location(
        self, to: str | int, text: str, tracker: CallbackDataT | None = None
    ) -> str:
        """
        Send a text message with button to request the user's location.

        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send with the button.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=InteractiveType.LOCATION_REQUEST_MESSAGE,
                    action={"name": "send_location"},
                    body=text,
                ),
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_contact(
        self,
        to: str | int,
        contact: Contact | Iterable[Contact],
        reply_to_message_id: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a contact/s to a WhatsApp user.

        Example:

            >>> from pywa_async.types import Contact
            >>> wa = WhatsApp(...)
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
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.CONTACTS,
                msg=tuple(c.to_dict() for c in contact)
                if isinstance(contact, Iterable)
                else (contact.to_dict(),),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_catalog(
        self,
        to: str | int,
        body: str,
        footer: str | None = None,
        thumbnail_product_sku: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send the business catalog to a WhatsApp user.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_catalog(
            ...     to='1234567890',
            ...     body='Check out our catalog!',
            ...     footer='Powered by PyWa',
            ...     thumbnail_product_sku='SKU123',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            thumbnail_product_sku: The thumbnail of this item will be used as the message's header image (optional, if
                not provided, the first item in the catalog will be used).
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=InteractiveType.CATALOG_MESSAGE,
                    action={
                        "name": "catalog_message",
                        **(
                            {
                                "parameters": {
                                    "thumbnail_product_retailer_id": thumbnail_product_sku,
                                }
                            }
                            if thumbnail_product_sku
                            else {}
                        ),
                    },
                    body=body,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_product(
        self,
        to: str | int,
        catalog_id: str,
        sku: str,
        body: str | None = None,
        footer: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a product from a business catalog to a WhatsApp user.
            - To send multiple products, use :py:func:`~pywa.client.WhatsApp.send_products`.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_product(
            ...     to='1234567890',
            ...     catalog_id='1234567890',
            ...     sku='SKU123',
            ...     body='Check out this product!',
            ...     footer='Powered by PyWa',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            catalog_id: The ID of the catalog to send the product from. (To get the catalog ID use
             :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager
             <https://business.facebook.com/commerce/>`_).
            sku: The product SKU to send.
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=InteractiveType.PRODUCT,
                    action={
                        "catalog_id": catalog_id,
                        "product_retailer_id": sku,
                    },
                    body=body,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def send_products(
        self,
        to: str | int,
        catalog_id: str,
        product_sections: Iterable[ProductsSection],
        title: str,
        body: str,
        footer: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send products from a business catalog to a WhatsApp user.
            - To send a single product, use :py:func:`~pywa.client.WhatsApp.send_product`.

        Example:

            >>> from pywa_async.types import ProductsSection
            >>> wa = WhatsApp(...)
            >>> wa.send_products(
            ...     to='1234567890',
            ...     catalog_id='1234567890',
            ...     title='Tech Products',
            ...     body='Check out our products!',
            ...     product_sections=[
            ...         ProductsSection(
            ...             title='Smartphones',
            ...             skus=['IPHONE12', 'GALAXYS21'],
            ...         ),
            ...         ProductsSection(
            ...             title='Laptops',
            ...             skus=['MACBOOKPRO', 'SURFACEPRO'],
            ...         ),
            ...     ],
            ...     footer='Powered by PyWa',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            catalog_id: The ID of the catalog to send the product from (To get the catalog ID use
             :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager
             <https://business.facebook.com/commerce/>`_).
            product_sections: The product sections to send (up to 30 products across all sections).
            title: The title of the product list (up to 60 characters).
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent message.
        """
        return (
            await self.api.send_message(
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=_get_interactive_msg(
                    typ=InteractiveType.PRODUCT_LIST,
                    action={
                        "catalog_id": catalog_id,
                        "sections": tuple(ps.to_dict() for ps in product_sections),
                    },
                    header={
                        "type": MessageType.TEXT,
                        "text": title,
                    },
                    body=body,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    async def mark_message_as_read(
        self,
        message_id: str,
    ) -> bool:
        """
        Mark a message as read.
            - You can mark incoming messages as read by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.mark_as_read` method.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.mark_message_as_read(message_id='wamid.XXX=')

        Args:
            message_id: The message ID to mark as read.

        Returns:
            Whether the message was marked as read.
        """
        return (await self.api.mark_message_as_read(message_id=message_id))["success"]

    async def upload_media(
        self,
        media: str | pathlib.Path | bytes | BinaryIO,
        mime_type: str | None = None,
        filename: str | None = None,
        dl_session: httpx.AsyncClient | None = None,
    ) -> str:
        """
        Upload media to WhatsApp servers.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.upload_media(
            ...     media='https://example.com/image.jpg',
            ...     mime_type='image/jpeg',
            ... )

        Args:
            media: The media to upload (can be a URL, bytes, or a file path).
            mime_type: The MIME type of the media (required if media is bytes or a file path).
            filename: The file name of the media (required if media is bytes).
            dl_session: A httpx session to use when downloading the media from a URL (optional, if not provided, a
             new session will be created).

        Returns:
            The media ID.

        Raises:
            ValueError:
                - If provided ``media`` is file path and the file does not exist.
                - If provided ``media`` is URL and the URL is invalid or media cannot be downloaded.
                - If provided ``media`` is bytes and ``filename`` or ``mime_type`` is not provided.
        """
        if isinstance(media, (str, pathlib.Path)):
            if (path := pathlib.Path(media)).is_file():
                file, filename, mime_type = (
                    open(path, "rb"),
                    filename or path.name,
                    mime_type or mimetypes.guess_type(path)[0],
                )
            elif (url := str(media)).startswith(("https://", "http://")):
                res = await (dl_session or httpx).get(url)
                try:
                    res.raise_for_status()
                except httpx.HTTPError as e:
                    raise ValueError(
                        f"An error occurred while downloading from {url}"
                    ) from e
                file, filename, mime_type = (
                    res.content,
                    filename or os.path.basename(media),
                    mime_type or res.headers["Content-Type"],
                )
            else:
                raise ValueError(f"File not found or invalid URL: {media}")
        else:
            file = media

        if filename is None:
            raise ValueError("`filename` is required if media is bytes")
        if mime_type is None:
            raise ValueError("`mime_type` is required if media is bytes")
        return (
            await self.api.upload_media(
                filename=filename,
                media=file,
                mime_type=mime_type,
            )
        )["id"]

    async def get_media_url(self, media_id: str) -> MediaUrlResponse:
        """
        Get the URL of a media.
            - The URL is valid for 5 minutes.
            - The media can be downloaded directly from the message using the :py:func:`~pywa.types.Message.download_media` method.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_media_url(media_id='wamid.XXX=')

        Args:
            media_id: The media ID.

        Returns:
            A MediaResponse object with the media URL.
        """
        res = await self.api.get_media_url(media_id=media_id)
        return MediaUrlResponse(
            _client=self,
            id=res["id"],
            url=res["url"],
            mime_type=res["mime_type"],
            sha256=res["sha256"],
            file_size=res["file_size"],
        )

    async def download_media(
        self,
        url: str,
        path: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> str | bytes:
        """
        Download a media file from WhatsApp servers.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.download_media(
            ...     url='https://mmg-fna.whatsapp.net/d/f/Amc.../v2/1234567890',
            ...     path='/home/david/Downloads',
            ...     filename='image.jpg',
            ... )

        Args:
            url: The URL of the media file (from :py:func:`~pywa.client.WhatsApp.get_media_url`).
            path: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to :py:func:`httpx.get`.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        content, mimetype = await self.api.get_media_bytes(media_url=url, **kwargs)
        if in_memory:
            return content
        if path is None:
            path = os.getcwd()
        if filename is None:
            filename = hashlib.sha256(url.encode()).hexdigest() + (
                mimetypes.guess_extension(mimetype) or ".bin"
            )
        path = os.path.join(path, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path

    async def get_business_phone_number(self) -> BusinessPhoneNumber:
        """
        Get the phone number of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_phone_number()

        Returns:
            The phone number object.
        """
        return BusinessPhoneNumber.from_dict(
            data=(
                await self.api.get_business_phone_number(
                    fields=tuple(
                        field.name for field in dataclasses.fields(BusinessPhoneNumber)
                    )
                )
            )
        )

    async def update_conversational_automation(
        self,
        enable_chat_opened: bool,
        ice_breakers: Iterable[str] | None = None,
        commands: Iterable[Command] | None = None,
    ) -> bool:
        """
        Update the conversational automation settings of the WhatsApp Business account.

        - You can receive the current conversational automation settings using :py:func:`~pywa.client.WhatsApp.get_business_phone_number` and accessing the ``conversational_automation`` attribute.
        - Read more about `Conversational Automation <https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers/conversational-components>`_.

        Args:
            enable_chat_opened: You can be notified whenever a WhatsApp user opens a chat with you for
             the first time. This can be useful if you want to reply to these users with a special welcome message of
             your own design (When enabled, you'll start receiving the :class:`ChatOpened` event).
            ice_breakers: Ice Breakers are customizable, tappable text strings that appear in a message thread the
             first time you chat with a user. For example, `Plan a trip` or `Create a workout plan`.
            commands: Commands are text strings that WhatsApp users can see by typing a forward slash in a message
             thread with your business.

        Returns:
            Whether the conversational automation settings were updated.
        """
        return (
            await self.api.update_conversational_automation(
                enable_welcome_message=enable_chat_opened,
                prompts=tuple(ice_breakers) if ice_breakers else None,
                commands=json.dumps([c.to_dict() for c in commands])
                if commands
                else None,
            )
        )["success"]

    async def get_business_profile(self) -> BusinessProfile:
        """
        Get the business profile of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_profile()

        Returns:
            The business profile.
        """
        return BusinessProfile.from_dict(
            data=(
                await self.api.get_business_profile(
                    fields=(
                        "about",
                        "address",
                        "description",
                        "email",
                        "profile_picture_url",
                        "websites",
                        "vertical",
                    )
                )
            )["data"][0]
        )

    async def set_business_public_key(
        self,
        public_key: str,
    ) -> bool:
        """
        Set the business public key of the WhatsApp Business account (required for end-to-end encryption in flows)

        Args:
            public_key: An public 2048-bit RSA Key in PEM format.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.set_business_public_key(
            ...     public_key=\"\"\"-----BEGIN PUBLIC KEY-----...\"\"\"
            ... )


        Returns:
            Whether the business public key was set.
        """
        return (await self.api.set_business_public_key(public_key=public_key))[
            "success"
        ]

    async def update_business_profile(
        self,
        about: str | None = _MISSING,
        address: str | None = _MISSING,
        description: str | None = _MISSING,
        email: str | None = _MISSING,
        profile_picture_handle: str | None = _MISSING,
        industry: Industry | None = _MISSING,
        websites: Iterable[str] | None = _MISSING,
    ) -> bool:
        """
        Update the business profile of the WhatsApp Business account.

        Example:

            >>> from pywa_async.types import Industry
            >>> wa = WhatsApp(...)
            >>> wa.update_business_profile(
            ...     about='This is a test business',
            ...     address='Menlo Park, 1601 Willow Rd, United States',
            ...     description='This is a test business',
            ...     email='test@test.com',
            ...     profile_picture_handle='1234567890',
            ...     industry=Industry.NOT_A_BIZ,
            ...     websites=('https://example.com', 'https://google.com'),
            ... )

        Args:
            about: The business's About text. This text appears in the business's profile, beneath its profile image,
             phone number, and contact buttons. (cannot be empty. must be between 1 and 139 characters. `markdown
             <https://faq.whatsapp.com/539178204879377>`_ is not supported. Hyperlinks can be included but
             will not render as clickable links.)
            address: Address of the business. Character limit 256.
            description: Description of the business. Character limit 512.
            email: The contact email address (in valid email format) of the business. Character limit 128.
            profile_picture_handle: Handle of the profile picture. This handle is generated when you upload the binary
             file for the profile picture to Meta using the `Resumable Upload API
             <https://developers.facebook.com/docs/graph-api/guides/upload>`_.
            industry: Industry of the business.
            websites: The URLs associated with the business. For instance, a website, Facebook Page, or Instagram.
             (You must include the ``http://`` or ``https://`` portion of the URL.
             There is a maximum of 2 websites with a maximum of 256 characters each.)

        Returns:
            Whether the business profile was updated.
        """
        data = {
            key: value or ""
            for key, value in {
                "about": about,
                "address": address,
                "description": description,
                "email": email,
                "profile_picture_handle": profile_picture_handle,
                "vertical": industry,
                "websites": websites,
            }.items()
            if value is not _MISSING
        }
        return (await self.api.update_business_profile(data))["success"]

    async def get_commerce_settings(self) -> CommerceSettings:
        """
        Get the commerce settings of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_commerce_settings()

        Returns:
            The commerce settings.
        """
        return CommerceSettings.from_dict(
            data=(await self.api.get_commerce_settings())["data"][0]
        )

    async def update_commerce_settings(
        self,
        is_catalog_visible: bool = None,
        is_cart_enabled: bool = None,
    ) -> bool:
        """
        Update the commerce settings of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.update_commerce_settings(
            ...     is_catalog_visible=True,
            ...     is_cart_enabled=True,
            ... )

        Args:
            is_catalog_visible: Whether the catalog is visible (optional).
            is_cart_enabled: Whether the cart is enabled (optional).

        Returns:
            Whether the commerce settings were updated.

        Raises:
            ValueError: If no arguments are provided.
        """
        data = {
            key: value
            for key, value in {
                "is_cart_enabled": is_cart_enabled,
                "is_catalog_visible": is_catalog_visible,
            }.items()
            if value is not None
        }
        if not data:
            raise ValueError("At least one argument must be provided")
        return (await self.api.update_commerce_settings(data))["success"]

    @staticmethod
    def _validate_waba_id_provided(func) -> Callable:
        """Internal decorator to validate the waba id is provided."""

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if self.business_account_id is None:
                raise ValueError(
                    f"You must provide the WhatsApp business account ID when using the `{func.__name__}` method.\n"
                    ">> You can provide it when initializing the client or by setting the `business_account_id` attr."
                )
            return await func(self, *args, **kwargs)

        return wrapper

    @_validate_waba_id_provided
    async def create_template(
        self,
        template: NewTemplate,
        placeholder: tuple[str, str] | None = None,
    ) -> TemplateResponse:
        """
        `'Create Templates' on developers.facebook.com
        <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates>`_.

        - This method requires the WhatsApp Business account ID to be provided when initializing the client.
        - To send a template, use :py:func:`~pywa.client.WhatsApp.send_template`.

        ATTENTION: In case of an errors, WhatsApp does not return a proper error message, instead, it returns a message
        of `invalid parameter` with error code of 100. You need to pay attention to the following:

        - The template name must be unique.
        - The limitiations of the characters in every field (all documented).
        - The order of the buttons.


        Templates can be created and managed in the
        `WhatsApp Message Templates <https://business.facebook.com/wa/manage/message-templates/>`_ dashboard.

        Example:

            >>> from pywa_async.types import NewTemplate as NewTemp
            >>> wa = WhatsApp(...)
            >>> wa.create_template(
            ...     template=NewTemp(
            ...         name='buy_new_iphone_x',
            ...         category=NewTemp.Category.MARKETING,
            ...         language=NewTemp.Language.ENGLISH_US,
            ...         header=NewTemp.Text('The New iPhone {15} is here!'),
            ...         body=NewTemp.Body('Buy now and use the code {WA_IPHONE_15} to get {15%} off!'),
            ...         footer=NewTemp.Footer('Powered by PyWa'),
            ...         buttons=[
            ...             NewTemp.UrlButton(title='Buy Now', url='https://example.com/shop/{iphone15}'),
            ...             NewTemp.PhoneNumberButton(title='Call Us', phone_number='1234567890'),
            ...             NewTemp.QuickReplyButton('Unsubscribe from marketing messages'),
            ...             NewTemp.QuickReplyButton('Unsubscribe from all messages'),
            ...         ],
            ...     ),
            ... )

        Example for Authentication Template:

            >>> from pywa_async.types import NewTemplate as NewTemp
            >>> wa = WhatsApp(...)
            >>> wa.create_template(
            ...     template=NewTemp(
            ...         name='auth_with_otp',
            ...         category=NewTemp.Category.AUTHENTICATION,
            ...         language=NewTemp.Language.ENGLISH_US,
            ...         body=NewTemp.AuthBody(
            ...             code_expiration_minutes=5,
            ...             add_security_recommendation=True,
            ...         ),
            ...         buttons=NewTemp.OTPButton(
            ...             otp_type=NewTemp.OTPButton.OtpType.ZERO_TAP,
            ...             title='Copy Code',
            ...             autofill_text='Autofill',
            ...             package_name='com.example.app',
            ...             signature_hash='1234567890ABCDEF1234567890ABCDEF12345678'
            ...         )
            ...     ),
            ... )

        Args:
            template: The template to create.
            placeholder: The placeholders start & end (optional, default: ``('{', '}')``)).

        Returns:
            The template created response. containing the template ID, status and category.
        """
        return TemplateResponse(
            **(
                await self.api.create_template(
                    waba_id=self.business_account_id,
                    template=template.to_dict(placeholder=placeholder),
                )
            )
        )

    async def send_template(
        self,
        to: str | int,
        template: Template,
        reply_to_message_id: str | None = None,
        tracker: CallbackDataT | None = None,
    ) -> str:
        """
        Send a template to a WhatsApp user.

        - To create a template, use :py:func:`~pywa.client.WhatsApp.create_template`.

        Example:

            >>> from pywa_async.types import Template as Temp
            >>> wa = WhatsApp(...)
            >>> wa.send_template(
            ...     to='1234567890',
            ...         template=Temp(
            ...         name='buy_new_iphone_x',
            ...         language=Temp.Language.ENGLISH_US,
            ...         header=Temp.TextValue(value='15'),
            ...         body=[
            ...             Temp.TextValue(value='John Doe'),
            ...             Temp.TextValue(value='WA_IPHONE_15'),
            ...             Temp.TextValue(value='15%'),
            ...         ],
            ...         buttons=[
            ...             Temp.UrlButtonValue(value='iphone15'),
            ...             Temp.QuickReplyButtonData(data='unsubscribe_from_marketing_messages'),
            ...             Temp.QuickReplyButtonData(data='unsubscribe_from_all_messages'),
            ...         ],
            ...     ),
            ... )

        Example for Authentication Template:

            >>> from pywa_async.types import Template as Temp
            >>> wa = WhatsApp(...)
            >>> wa.send_template(
            ...     to='1234567890',
            ...         template=Temp(
            ...         name='auth_with_otp',
            ...         language=Temp.Language.ENGLISH_US,
            ...         buttons=Temp.OTPButtonCode(code='123456'),
            ...     ),
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            template: The template to send.
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The message ID of the sent template.

        Raises:

        """
        is_url = None
        match type(template.header):
            case Template.Image:
                is_url, template.header.image = await _resolve_media_param(
                    wa=self,
                    media=template.header.image,
                    mime_type=template.header.mime_type,
                    media_type=MessageType.IMAGE,
                    filename=None,
                )
            case Template.Document:
                is_url, template.header.document = await _resolve_media_param(
                    wa=self,
                    media=template.header.document,
                    mime_type="application/pdf",  # the only supported mime type in template's document header
                    filename=template.header.filename,
                    media_type=None,
                )
            case Template.Video:
                is_url, template.header.video = await _resolve_media_param(
                    wa=self,
                    media=template.header.video,
                    mime_type=template.header.mime_type,
                    media_type=MessageType.VIDEO,
                    filename=None,
                )
        return (
            await self.api.send_message(
                to=str(to),
                typ="template",
                msg=template.to_dict(is_header_url=is_url),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=_resolve_tracker_param(tracker),
            )
        )["messages"][0]["id"]

    @_validate_waba_id_provided
    async def create_flow(
        self,
        name: str,
        categories: Iterable[FlowCategory | str],
        clone_flow_id: str | None = None,
        endpoint_uri: str | None = None,
    ) -> str:
        """
        Create a flow.

        - This method requires the WhatsApp Business account ID to be provided when initializing the client.
        - New Flows are created in :class:`FlowStatus.DRAFT` status.
        - To update the flow json, use :py:func:`~pywa.client.WhatsApp.update_flow`.
        - To send a flow, use :py:func:`~pywa.client.WhatsApp.send_flow`.

        Args:
            name: The name of the flow.
            categories: The categories of the flow.
            clone_flow_id: The flow ID to clone (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from Flow 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a Flow with version below 3.0.

        Example:

            >>> from pywa_async.types.flows import FlowCategory
            >>> wa = WhatsApp(...)
            >>> wa.create_flow(
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER]
            ... )

        Returns:
            The flow ID.

        Raises:
            FlowBlockedByIntegrity: If you can't create a flow because of integrity issues.
        """
        return (
            await self.api.create_flow(
                name=name,
                categories=tuple(map(str, categories)),
                clone_flow_id=clone_flow_id,
                endpoint_uri=endpoint_uri,
                waba_id=self.business_account_id,
            )
        )["id"]

    async def update_flow_metadata(
        self,
        flow_id: str | int,
        *,
        name: str | None = None,
        categories: Iterable[FlowCategory | str] | None = None,
        endpoint_uri: str | None = None,
    ) -> bool:
        """
        Update the metadata of a flow.

        Args:
            flow_id: The flow ID.
            name: The name of the flow (optional).
            categories: The new categories of the flow (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from FlowJSON 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a FlowJSON with version below 3.0.

        Example:

            >>> from pywa_async.types.flows import FlowCategory
            >>> wa = WhatsApp(...)
            >>> wa.update_flow_metadata(
            ...     flow_id='1234567890',
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER],
            ...     endpoint_uri='https://my-api-server/feedback_flow'
            ... )

        Returns:
            Whether the flow was updated.

        Raises:
            ValueError: If neither ``name``, ``categories`` or ``endpoint_uri`` are provided.
        """
        if name is None and categories is None and endpoint_uri is None:
            raise ValueError("At least one argument must be provided")
        return (
            await self.api.update_flow_metadata(
                flow_id=str(flow_id),
                name=name,
                categories=tuple(map(str, categories)) if categories else None,
                endpoint_uri=endpoint_uri,
            )
        )["success"]

    async def update_flow_json(
        self,
        flow_id: str | int,
        flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO,
    ) -> tuple[bool, tuple[FlowValidationError, ...]]:
        """
        Update the json of a flow.

        Args:
            flow_id: The flow ID.
            flow_json: The new json of the flow. Can be a FlowJSON object, dict, json string, json file path or json bytes.

        Examples:

            >>> wa = WhatsApp(...)

            - Using a Flow object:

            >>> from pywa_async.types.flows import *
            >>> wa.update_flow_json(
            ...     flow_id='1234567890',
            ...     flow_json=FlowJSON(version='2.1', screens=[Screen(...)])
            ... )

            - From a json file path:

            >>> wa.update_flow_json(
            ...     flow_id='1234567890',
            ...     flow_json="/home/david/feedback_flow.json"
            ... )

            - From a json string:

            >>> wa.update_flow_json(
            ...     flow_id='1234567890',
            ...     flow_json=\"\"\"{"version": "2.1", "screens": [...]}\"\"\"
            ... )


        Returns:
            A tuple of (success, validation_errors).

        Raises:
            FlowUpdatingError: If the flow json is invalid or the flow is already published.
        """
        json_str = None
        to_dump = None
        if isinstance(flow_json, (str, pathlib.Path)):
            as_path = pathlib.Path(flow_json)
            try:
                if as_path.is_file():
                    with open(as_path, "r") as f:
                        json_str = f.read()
            except OSError:  # file name too long or other OS error
                pass
        elif isinstance(flow_json, FlowJSON):
            to_dump = flow_json.to_dict()
        elif isinstance(flow_json, dict):
            to_dump = flow_json
        elif isinstance(flow_json, bytes):
            json_str = flow_json.decode()

        if to_dump is not None:
            json_str = json.dumps(to_dump)
        res = await self.api.update_flow_json(
            flow_id=str(flow_id), flow_json=json_str or flow_json
        )
        return res["success"], tuple(
            FlowValidationError.from_dict(data) for data in res["validation_errors"]
        )

    async def publish_flow(
        self,
        flow_id: str | int,
    ) -> bool:
        """
        This request updates the status of the Flow to "PUBLISHED".

        - This action is not reversible.
        - The Flow and its assets become immutable once published.
        - To update the Flow after that, you must create a new Flow. You specify the existing Flow ID as the clone_flow_id parameter while creating to copy the existing flow.

            You can publish your Flow once you have ensured that:

            - All validation errors and publishing checks have been resolved.
            - The Flow meets the design principles of WhatsApp Flows
            - The Flow complies with WhatsApp Terms of Service, the WhatsApp Business Messaging Policy and, if applicable, the WhatsApp Commerce Policy

        Args:
            flow_id: The flow ID.

        Returns:
            Whether the flow was published.

        Raises:
            FlowPublishingError: If the flow has validation errors or not all publishing checks have been resolved.
        """
        return (await self.api.publish_flow(flow_id=str(flow_id)))["success"]

    async def delete_flow(
        self,
        flow_id: str | int,
    ) -> bool:
        """
        While a Flow is in DRAFT status, it can be deleted.

        Args:
            flow_id: The flow ID.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If the flow is already published.
        """
        return (await self.api.delete_flow(flow_id=str(flow_id)))["success"]

    async def deprecate_flow(
        self,
        flow_id: str | int,
    ) -> bool:
        """
        Once a Flow is published, it cannot be modified or deleted, but can be marked as deprecated.

        Args:
            flow_id: The flow ID.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If the flow is not published or already deprecated.
        """
        return (await self.api.deprecate_flow(flow_id=str(flow_id)))["success"]

    async def get_flow(
        self,
        flow_id: str | int,
        invalidate_preview: bool = True,
    ) -> FlowDetails:
        """
        Get the details of a flow.

        Args:
            flow_id: The flow ID.
            invalidate_preview: Whether to invalidate the preview (optional, default: True).

        Returns:
            The details of the flow.
        """
        return FlowDetails.from_dict(
            data=(
                await self.api.get_flow(
                    flow_id=str(flow_id),
                    fields=_get_flow_fields(invalidate_preview=invalidate_preview),
                )
            ),
            client=self,
        )

    @_validate_waba_id_provided
    async def get_flows(
        self,
        invalidate_preview: bool = True,
    ) -> tuple[FlowDetails, ...]:
        """
        Get the details of all flows belonging to the WhatsApp Business account.

        - This method requires the WhatsApp Business account ID to be provided when initializing the client.

        Args:
            invalidate_preview: Whether to invalidate the preview (optional, default: True).

        Returns:
            The details of all flows.
        """
        return tuple(
            FlowDetails.from_dict(data=data, client=self)
            for data in (
                await self.api.get_flows(
                    waba_id=self.business_account_id,
                    fields=_get_flow_fields(invalidate_preview=invalidate_preview),
                )
            )["data"]
        )

    async def get_flow_assets(
        self,
        flow_id: str | int,
    ) -> tuple[FlowAsset, ...]:
        """
        Get all assets attached to a specified Flow.

        Args:
            flow_id: The flow ID.

        Returns:
            The assets of the flow.
        """
        return tuple(
            FlowAsset.from_dict(data)
            for data in (
                await self.api.get_flow_assets(
                    flow_id=str(flow_id),
                )
            )["data"]
        )

    async def register_phone_number(
        self, pin: int | str, data_localization_region: str | None = None
    ) -> bool:
        """
        Register a Business Phone Number

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/registration>`_

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.register_phone_number(password='111111', data_localization_region='US')

        Args:
            pin: If your verified business phone number already has two-step verification enabled,
             set this value to your number's 6-digit two-step verification PIN.
             If you cannot recall your PIN, you can
             `uptdate <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/two-step-verification#updating-verification-code>`_ it.
            data_localization_region: If included, enables
             `local storage <https://developers.facebook.com/docs/whatsapp/cloud-api/overview/local-storage/>`_ on the
             business phone number.
             Value must be a 2-letter ISO 3166 country code (e.g. ``IN``) indicating the country where you
             want data-at-rest to be stored.

        Returns:
            The success of the registration.
        """

        return (
            await self.api.register_phone_number(
                pin=str(pin), data_localization_region=data_localization_region
            )
        )["success"]


async def _resolve_media_param(
    wa: WhatsApp,
    media: str | pathlib.Path | bytes | BinaryIO,
    mime_type: str | None,
    filename: str | None,
    media_type: Literal[
        MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.STICKER
    ]
    | None,
) -> tuple[bool, str]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``media_id_or_url``).
    """
    if isinstance(media, (str, pathlib.Path)):
        if str(media).startswith(("https://", "http://")):
            return True, media
        elif str(media).isdigit() and not pathlib.Path(media).is_file():
            return False, media  # assume it's a media ID
    # assume its bytes or a file path
    return False, await wa.upload_media(
        media=media,
        mime_type=mime_type,
        filename=_media_types_default_filenames.get(media_type, filename),
    )
