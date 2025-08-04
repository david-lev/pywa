from __future__ import annotations


"""The WhatsApp Async client."""

__all__ = ["WhatsApp"]

import datetime
import functools
import hashlib
import json
import logging
import mimetypes
import pathlib
from types import ModuleType
from typing import BinaryIO, Iterable, Literal, Any

import httpx

from pywa.client import (
    WhatsApp as _WhatsApp,
    _DEFAULT_VERIFY_DELAY_SEC,
    _AuthenticationTemplates,
    _TemplateUpdate,
)  # noqa MUST BE IMPORTED FIRST
from pywa.types.base_update import BaseUpdate
from . import _helpers as helpers
from . import utils
from .api import GraphAPIAsync
from .listeners import _AsyncListeners
from .server import Server
from .types import (
    BusinessProfile,
    Button,
    URLButton,
    VoiceCallButton,
    CallPermissionRequestButton,
    CommerceSettings,
    Contact,
    Industry,
    MediaUrlResponse,
    Message,
    ProductsSection,
    SectionList,
    Template,
    FlowButton,
    MessageType,
    BusinessPhoneNumber,
    Command,
    CallbackData,
    QRCode,
    FlowMetricName,
    FlowMetricGranularity,
    FlowRequest,
    Result,
    Pagination,
    User,
    MessageStatus,
    CallbackButton,
    CallbackSelection,
    ChatOpened,
    FlowCompletion,
    UserMarketingPreferences,
    TemplateStatusUpdate,
    Image,
    Video,
    Document,
    Sticker,
    Audio,
    BusinessPhoneNumberSettings,
    CallConnect,
    CallTerminate,
    CallStatus,
    TemplateCategoryUpdate,
    TemplateQualityUpdate,
    TemplateComponentsUpdate,
    PhoneNumberChange,
    IdentityChange,
    CallPermissionUpdate,
)
from .handlers import (
    Handler,
    MessageHandler,
    MessageStatusHandler,
    CallbackButtonHandler,
    CallbackSelectionHandler,
    ChatOpenedHandler,
    FlowCompletionHandler,
    TemplateStatusUpdateHandler,
    UserMarketingPreferencesHandler,
    CallConnectHandler,
    CallTerminateHandler,
    CallStatusHandler,
    CallPermissionUpdateHandler,
    TemplateCategoryUpdateHandler,
    TemplateQualityUpdateHandler,
    TemplateComponentsUpdateHandler,
    PhoneNumberChangeHandler,
    IdentityChangeHandler,
)
from .types.flows import (
    FlowCategory,
    FlowJSON,
    FlowDetails,
    FlowAsset,
    CreatedFlow,
    MigrateFlowsResponse,
)
from .types.templates import (
    TemplatesResult,
    TemplateDetails,
    TemplateCategory,
    TemplateLanguage,
    QualityScoreType,
    TemplateBaseComponent,
    ParamFormat,
    TemplatesCompareResult,
    MigrateTemplatesResult,
    CreatedTemplate,
    LibraryTemplate,
    TemplateStatus,
    TemplateUnpauseResult,
    BaseOTPButton,
    CreatedTemplates,
    AuthenticationBody,
    AuthenticationFooter,
    Buttons,
    UpdatedTemplate,
)
from .types.media import Media
from .types.flows import FlowJSONUpdateResult
from .types.calls import CallPermissions, SessionDescription
from .types.others import (
    InteractiveType,
    UsersBlockedResult,
    UsersUnblockedResult,
    SuccessResult,
    WhatsAppBusinessAccount,
)
from .types.sent_update import SentMessage, SentTemplate, InitiatedCall
from .utils import FastAPI, Flask

_logger = logging.getLogger(__name__)


class WhatsApp(Server, _AsyncListeners, _WhatsApp):
    _api_cls = GraphAPIAsync
    _flow_req_cls = FlowRequest
    _usr_cls = User
    _httpx_client = httpx.AsyncClient
    _async_allowed = True
    api: GraphAPIAsync  # IDE type hinting

    _handlers_to_updates: dict[type[Handler], BaseUpdate] = {
        MessageHandler: Message,
        MessageStatusHandler: MessageStatus,
        CallbackButtonHandler: CallbackButton,
        CallbackSelectionHandler: CallbackSelection,
        ChatOpenedHandler: ChatOpened,
        PhoneNumberChangeHandler: PhoneNumberChange,
        IdentityChangeHandler: IdentityChange,
        FlowCompletionHandler: FlowCompletion,
        TemplateStatusUpdateHandler: TemplateStatusUpdate,
        TemplateCategoryUpdateHandler: TemplateCategoryUpdate,
        TemplateQualityUpdateHandler: TemplateQualityUpdate,
        TemplateComponentsUpdateHandler: TemplateComponentsUpdate,
        UserMarketingPreferencesHandler: UserMarketingPreferences,
        CallConnectHandler: CallConnect,
        CallTerminateHandler: CallTerminate,
        CallStatusHandler: CallStatus,
        CallPermissionUpdateHandler: CallPermissionUpdate,
    }
    """A dictionary that maps handler types to their respective update constructors."""

    _msg_fields_to_objects_constructors = (
        _WhatsApp._msg_fields_to_objects_constructors
        | dict(
            image=Image.from_dict,
            video=Video.from_dict,
            sticker=Sticker.from_dict,
            document=Document.from_dict,
            audio=Audio.from_dict,
        )
    )
    """A mapping of message types to their respective constructors."""

    def __init__(
        self,
        phone_id: str | int | None = None,
        token: str = None,
        *,
        session: httpx.AsyncClient | None = None,
        server: Flask | FastAPI | None = utils.MISSING,
        webhook_endpoint: str = "/",
        verify_token: str | None = None,
        filter_updates: bool = True,
        continue_handling: bool = False,
        skip_duplicate_updates: bool = True,
        validate_updates: bool = True,
        business_account_id: str | int | None = None,
        callback_url: str | None = None,
        callback_url_scope: utils.CallbackURLScope = utils.CallbackURLScope.APP,
        webhook_fields: Iterable[str] | None = None,
        app_id: int | None = None,
        app_secret: str | None = None,
        webhook_challenge_delay: int = _DEFAULT_VERIFY_DELAY_SEC,
        business_private_key: str | None = None,
        business_private_key_password: str | None = None,
        flows_request_decryptor: utils.FlowRequestDecryptor
        | None = utils.default_flow_request_decryptor,
        flows_response_encryptor: utils.FlowResponseEncryptor
        | None = utils.default_flow_response_encryptor,
        api_version: str
        | int
        | float
        | Literal[utils.Version.GRAPH_API] = utils.Version.GRAPH_API,
        handlers_modules: Iterable[ModuleType] | None = None,
    ) -> None:
        """
        The WhatsApp client.
            - Full documentation on `pywa.readthedocs.io <https://pywa.readthedocs.io>`_.

        Example without webhook:

            >>> from pywa_async import WhatsApp
            >>> wa = WhatsApp(phone_id="1234567890",token="EAADKQl9oJxx")
            >>> await wa.send_message("1234567890", "Hello from PyWa!")

        Example with webhook (using ``FastAPI``):

            >>> import pywa_async, fastapi
            >>> fastapi_app = fastapi.FastAPI()
            >>> wa = pywa_async.WhatsApp(
            ...     phone_id="1234567890",
            ...     token="EAADKQl9oJxx",
            ...     server=fastapi_app,
            ...     callback_url='https://pywa.ngrok.io',
            ...     verify_token="XYZ123",
            ...     app_id=1234567890,
            ...     app_secret="my_app_secret",
            ... )

            >>> @wa.on_message(filters.text)
            ... async def new_message(_: WhatsApp, msg: Message):
            ...     await msg.reply("Hello from PyWa!")

            ``$ fastapi dev wa.py`` see `uvicorn docs <https://www.uvicorn.org/#command-line-options>`_ for more options (port, host, reload, etc.)

        Args:
            phone_id: The Phone number ID to send messages from (if you manage multiple WhatsApp business accounts
             (e.g. partner solutions), you can specify the phone ID when sending messages, optional).
            token: The token to use for WhatsApp Cloud API (In production, you should
             `use permanent token <https://developers.facebook.com/docs/whatsapp/business-management-api/get-started>`_).
            api_version: The API version of the WhatsApp Cloud API (default to the latest version).
            session: The session to use for api requests (default: new ``httpx.AsyncClient``, For cases where you want to
             use a custom session, e.g. for proxy support. Do not use the same session across multiple WhatsApp clients!).
            server: The Flask or FastAPI app instance to use for the webhook. required when you want to handle incoming
             updates. pass `None` to insert the updates with the :meth:`webhook_update_handler`.
            callback_url: The server URL to register (without endpoint. optional).
            callback_url_scope: The scope of the callback URL to register (default: ``APP``).
            verify_token: A challenge string (Required when ``server`` is provided. The verify token can be any string.
             It is used to challenge the webhook endpoint to verify that the endpoint is valid).
            webhook_challenge_delay: The delay (in seconds, default to ``3``) to wait for the verify token to be sent to the server (optional,
             for cases where the server/network is slow or the server is taking a long time to start).
            webhook_fields: The fields to register for the callback URL (optional, if not provided, all supported fields will be
             registered. modify this if you want to reduce the number of unused requests to your server).
             See `Availble fields <https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-whatsapp#available-subscription-fields>`_.
            app_id: The ID of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
             (optional, required when registering a ``callback_url``).
            app_secret: The secret of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
             (optional, recomended for validating updates, required when registering a ``callback_url``).
            webhook_endpoint: The endpoint to listen for incoming messages (if you're using the server for another purpose,
             you can change this to avoid conflicts).
            filter_updates: Whether to filter out user updates that are not sent to this phone_id (default: ``True``, does
             not apply to raw updates or updates that are not user-related).
            helpers.resolve_arg(wa=self, value=waba_id, method_arg="waba_id", client_arg="business_account_id"): The WhatsApp business account ID (WABA ID) that owns the phone ID (optional, required for some API
             methods).
            business_private_key: The global private key to use in the ``flows_request_decryptor``
            business_private_key_password: The global private key password (if needed) to use in the ``flows_request_decryptor``
            flows_request_decryptor: The global flows requests decryptor implementation to use to decrypt Flows requests.
            flows_response_encryptor: The global flows response encryptor implementation to use to encrypt Flows responses.
            continue_handling: Whether to continue handling updates after a handler or listener has been found (default: ``False``).
            skip_duplicate_updates: Whether to skip duplicate updates (default: ``True``).
            validate_updates: Whether to validate updates payloads (default: ``True``, ``app_secret`` required).
            handlers_modules: Modules to load handlers from.
        """
        super().__init__(
            phone_id=phone_id,
            token=token,
            api_version=api_version,
            session=session,
            server=server,
            webhook_endpoint=webhook_endpoint,
            verify_token=verify_token,
            filter_updates=filter_updates,
            business_account_id=business_account_id,
            callback_url=callback_url,
            callback_url_scope=callback_url_scope,
            webhook_fields=webhook_fields,
            app_id=app_id,
            app_secret=app_secret,
            webhook_challenge_delay=webhook_challenge_delay,
            business_private_key=business_private_key,
            business_private_key_password=business_private_key_password,
            flows_request_decryptor=flows_request_decryptor,
            flows_response_encryptor=flows_response_encryptor,
            continue_handling=continue_handling,
            skip_duplicate_updates=skip_duplicate_updates,
            validate_updates=validate_updates,
            handlers_modules=handlers_modules,
        )

    def __repr__(self):
        return f"WhatsAppAsync(phone_id={self.phone_id!r})"

    async def send_message(
        self,
        to: str | int,
        text: str,
        header: str | None = None,
        footer: str | None = None,
        buttons: (
            Iterable[Button]
            | URLButton
            | VoiceCallButton
            | CallPermissionRequestButton
            | SectionList
            | FlowButton
            | None
        ) = None,
        *,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Text messages are messages containing text and an optional link preview.

        - You can have the WhatsApp client attempt to render a preview of the first URL in the body text string, if it contains one. URLs must begin with ``http://`` or ``https://``. If multiple URLs are in the body text string, only the first URL will be rendered. If omitted, or if unable to retrieve a link preview, a clickable link will be rendered instead.
        - See `Text messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages>`_.
        - See `Markdown <https://faq.whatsapp.com/539178204879377>`_ for formatting text messages.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.send_message(
            ...     to="1234567890",
            ...     text="Hello from PyWa! (https://github.com/david-lev/pywa)",
            ...     preview_url=True,
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
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        if not buttons:
            return SentMessage.from_sent_update(
                client=self,
                update=await self.api.send_message(
                    sender=sender,
                    to=str(to),
                    typ=MessageType.TEXT,
                    msg={"body": text, "preview_url": preview_url},
                    reply_to_message_id=reply_to_message_id,
                    biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
                ),
                from_phone_id=sender,
            )
        typ, kb, sent_kw = helpers.resolve_buttons_param(buttons)
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
            **sent_kw,
        )

    send_text = send_message  # alias

    async def send_image(
        self,
        to: str | int,
        image: str | Media | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        reply_to_message_id: str | None = None,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Image messages are messages that display a single image and an optional caption.

        - See `Image messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages>`_.
        - See `Supported image formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages#supported-image-formats>`_.
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
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent image message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        is_url, image = await helpers.resolve_media_param(
            wa=self,
            media=image,
            mime_type=mime_type,
            filename=None,
            media_type=MessageType.IMAGE,
            phone_id=sender,
        )

        if not buttons:
            return SentMessage.from_sent_update(
                client=self,
                update=await self.api.send_message(
                    sender=sender,
                    to=str(to),
                    typ=MessageType.IMAGE,
                    msg=helpers.get_media_msg(
                        media_id_or_url=image, is_url=is_url, caption=caption
                    ),
                    reply_to_message_id=reply_to_message_id,
                    biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
                ),
                from_phone_id=sender,
            )
        if not caption:
            raise ValueError(
                "A caption must be provided when sending an image with buttons."
            )
        typ, kb, sent_kw = helpers.resolve_buttons_param(buttons)
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
            **sent_kw,
        )

    async def send_video(
        self,
        to: str | int,
        video: str | Media | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        mime_type: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Video messages display a thumbnail preview of a video image with an optional caption. When the WhatsApp user taps the preview, it loads the video and displays it to the user.

        - Only H.264 video codec and AAC audio codec supported. Single audio stream or no audio stream only.
        - See `Video messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages>`_.
        - See `Supported video formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages#supported-video-formats>`_.

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
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent video.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        is_url, video = await helpers.resolve_media_param(
            wa=self,
            media=video,
            mime_type=mime_type,
            filename=None,
            media_type=MessageType.VIDEO,
            phone_id=sender,
        )
        if not buttons:
            return SentMessage.from_sent_update(
                client=self,
                update=await self.api.send_message(
                    sender=sender,
                    to=str(to),
                    typ=MessageType.VIDEO,
                    msg=helpers.get_media_msg(
                        media_id_or_url=video, is_url=is_url, caption=caption
                    ),
                    reply_to_message_id=reply_to_message_id,
                    biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
                ),
                from_phone_id=sender,
            )
        if not caption:
            raise ValueError(
                "A caption must be provided when sending a video with buttons."
            )
        typ, kb, sent_kw = helpers.resolve_buttons_param(buttons)
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
            **sent_kw,
        )

    async def send_document(
        self,
        to: str | int,
        document: str | Media | pathlib.Path | bytes | BinaryIO,
        filename: str | None = None,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        mime_type: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Document messages are messages that display a document icon, linked to a document, that a WhatsApp user can tap to download.

        - See `Document messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages>`_.
        - See `Supported document types <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages#supported-document-types>`_.

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
            filename: Document filename, with extension. The WhatsApp client will use an appropriate file type icon based on the extension.
            caption: The caption of the document (required when sending a document with buttons,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the document (optional).
            reply_to_message_id: The message ID to reply to (optional, only works if buttons provided).
            mime_type: The mime type of the document (optional, required when sending a document as bytes or a file
             object, or file path that does not have an extension).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent document.
        """

        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        is_url, document = await helpers.resolve_media_param(
            wa=self,
            media=document,
            mime_type=mime_type,
            filename=filename,
            media_type=None,
            phone_id=sender,
        )
        if not buttons:
            return SentMessage.from_sent_update(
                client=self,
                update=await self.api.send_message(
                    sender=sender,
                    to=str(to),
                    typ=MessageType.DOCUMENT,
                    msg=helpers.get_media_msg(
                        media_id_or_url=document,
                        is_url=is_url,
                        caption=caption,
                        filename=filename,
                    ),
                    reply_to_message_id=reply_to_message_id,
                    biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
                ),
                from_phone_id=sender,
            )
        if not caption:
            raise ValueError(
                "A caption must be provided when sending a document with buttons."
            )
        typ, kb, sent_kw = helpers.resolve_buttons_param(buttons)
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
                    typ=typ,
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
            **sent_kw,
        )

    async def send_audio(
        self,
        to: str | int,
        audio: str | Media | pathlib.Path | bytes | BinaryIO,
        *,
        mime_type: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Audio messages display an audio icon and a link to an audio file. When the WhatsApp user taps the icon, the WhatsApp client loads and plays the audio file.

        - See `Audio messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/audio-messages>`_.
        - See `Supported audio formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/audio-messages#supported-audio-formats>`_.

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
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent audio file.
        """

        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        is_url, audio = await helpers.resolve_media_param(
            wa=self,
            media=audio,
            mime_type=mime_type,
            filename=None,
            media_type=MessageType.AUDIO,
            phone_id=sender,
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.AUDIO,
                msg=helpers.get_media_msg(media_id_or_url=audio, is_url=is_url),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_sticker(
        self,
        to: str | int,
        sticker: str | Media | pathlib.Path | bytes | BinaryIO,
        *,
        mime_type: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Sticker messages display animated or static sticker images in a WhatsApp message.

        - A static sticker needs to be 512x512 pixels and cannot exceed 100 KB.
        - An animated sticker must be 512x512 pixels and cannot exceed 500 KB.
        - See `Sticker messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/sticker-messages>`_.
        - See `Supported sticker formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/sticker-messages#supported-sticker-formats>`_.

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
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """

        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        is_url, sticker = await helpers.resolve_media_param(
            wa=self,
            media=sticker,
            mime_type=mime_type,
            filename=None,
            media_type=MessageType.STICKER,
            phone_id=sender,
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.STICKER,
                msg=helpers.get_media_msg(media_id_or_url=sticker, is_url=is_url),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_reaction(
        self,
        to: str | int,
        emoji: str,
        message_id: str,
        *,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Reaction messages are emoji-reactions that you can apply to a previous WhatsApp user message that you have received.

        - When sending a reaction message, only a :class:`MessageStatus` update (``type`` set to ``SENT``) will be triggered; ``DELIVERED`` and ``READ`` updates will not be triggered.
        - You can react to incoming messages by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.react` method on every update.

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
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The message ID of the reaction (You can't use this message id to remove the reaction or perform any other
            action on it. instead, use the message ID of the message you reacted to).
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.REACTION,
                msg={"emoji": emoji, "message_id": message_id},
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def remove_reaction(
        self,
        to: str | int,
        message_id: str,
        *,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Remove reaction from a message.

        - You can remove reactions from incoming messages by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.unreact` method on every update.

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
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The message ID of the reaction (You can't use this message id to re-react or perform any other action on it.
            instead, use the message ID of the message you unreacted to).
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.REACTION,
                msg={"emoji": "", "message_id": message_id},
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_location(
        self,
        to: str | int,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Location messages allow you to send a location's latitude and longitude coordinates to a WhatsApp user.

        - Read more about `Location messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/location-messages>`_.

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
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent location.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.LOCATION,
                msg={
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name,
                    "address": address,
                },
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def request_location(
        self,
        to: str | int,
        text: str,
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Location request messages display body text and a send location button. When a WhatsApp user taps the button, a location sharing screen appears which the user can then use to share their location.

        - Once the user shares their location, a :class:`Message` update is triggered, containing the user's location details.
        - Read more about `Location request messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/location-request-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.request_location(
            ...     to='1234567890',
            ...     text='Please share your location with us.',
            ... )

        Args:
            to: The phone ID of the WhatsApp user.
            text: The text to send with the button.
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
                    typ=InteractiveType.LOCATION_REQUEST_MESSAGE,
                    action={"name": "send_location"},
                    body=text,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_contact(
        self,
        to: str | int,
        contact: Contact | Iterable[Contact],
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Contacts messages allow you to send rich contact information directly to WhatsApp users, such as names, phone numbers, physical addresses, and email addresses.
        When a WhatsApp user taps the message's profile arrow, it displays the contact's information in a profile view:

        - Each message can include information for up to 257 contacts, although it is recommended to send fewer for usability and negative feedback reasons.

        - See `Contacts messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/contacts-messages>`_.

        Example:

            >>> from pywa.types import Contact
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
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.CONTACTS,
                msg=tuple(c.to_dict() for c in contact)
                if isinstance(contact, Iterable)
                else (contact.to_dict(),),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_catalog(
        self,
        to: str | int,
        body: str,
        footer: str | None = None,
        *,
        thumbnail_product_sku: str | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Catalog messages are messages that allow you to showcase your product catalog entirely within WhatsApp.

        Catalog messages display a product thumbnail header image of your choice, custom body text, a fixed text header, a fixed text sub-header, and a View catalog button.

        - When a customer taps the View catalog button, your product catalog appears within WhatsApp.
        - You must have `inventory uploaded to Meta <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/upload-inventory>`_ in an ecommerce catalog `connected to your WhatsApp Business Account <https://www.facebook.com/business/help/158662536425974>`_.
        - Read more about `Catalog messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#catalog-messages>`_.

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
            thumbnail_product_sku: Item SKU number. Labeled as Content ID in the Commerce Manager. The thumbnail of this item will be used as the message's header image. If omitted, the product image of the first item in your catalog will be used.
            reply_to_message_id: The message ID to reply to (optional).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_product(
        self,
        to: str | int,
        catalog_id: str,
        sku: str,
        body: str | None = None,
        footer: str | None = None,
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Send a product from a business catalog to a WhatsApp user.

        - To send multiple products, use :py:func:`~pywa.client.WhatsApp.send_products`.
        - See `Product messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#product-messages>`_.

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
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
                    typ=InteractiveType.PRODUCT,
                    action={
                        "catalog_id": catalog_id,
                        "product_retailer_id": sku,
                    },
                    body=body,
                    footer=footer,
                ),
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def send_products(
        self,
        to: str | int,
        catalog_id: str,
        product_sections: Iterable[ProductsSection],
        title: str,
        body: str,
        footer: str | None = None,
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Send products from a business catalog to a WhatsApp user.

        - To send a single product, use :py:func:`~pywa.client.WhatsApp.send_product`.
        - See `Product messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#product-messages>`_.

        Example:

            >>> from pywa.types import ProductsSection
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
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        return SentMessage.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ=MessageType.INTERACTIVE,
                msg=helpers.get_interactive_msg(
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
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def mark_message_as_read(
        self,
        message_id: str,
        *,
        sender: str | int | None = None,
    ) -> SuccessResult:
        """
        When you get a :class:`Message`, you can use the msg.id value to mark the message as read.

        - You can mark incoming messages as read by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.mark_as_read` method or indicate typing by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.indicate_typing` method on every update.
        - It's good practice to mark an incoming messages as read within 30 days of receipt. Marking a message as read will also mark earlier messages in the thread as read.
        - Read more about `Mark messages as read <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/mark-message-as-read>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.mark_message_as_read(message_id='wamid.XXX=')

        Args:
            message_id: The message ID to mark as read.
            sender: The phone ID (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the message was marked as read.
        """
        return SuccessResult.from_dict(
            await self.api.mark_message_as_read(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=sender,
                    method_arg="sender",
                    client_arg="phone_id",
                ),
                message_id=message_id,
            )
        )

    async def indicate_typing(
        self,
        message_id: str,
        *,
        sender: str | int | None = None,
    ) -> SuccessResult:
        """
        When you get a :class:`Message`, you can use the msg.id value to mark the message as read and display a typing indicator so the WhatsApp user knows you are preparing a response. This is good practice if it will take you a few seconds to respond.

        - You can indicate typing by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.indicate_typing` method on every update.
        - The typing indicator will be dismissed once you respond, or after 25 seconds, whichever comes first. To prevent a poor user experience, only display a typing indicator if you are going to respond.
        - Read more about `Typing indicators <https://developers.facebook.com/docs/whatsapp/cloud-api/typing-indicators>`_.

        Args:
            message_id: The message ID to mark as read and display a typing indicator.
            sender: The phone ID (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the message was marked as read and the typing indicator was displayed.
        """
        return SuccessResult.from_dict(
            await self.api.set_indicator(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=sender,
                    method_arg="sender",
                    client_arg="phone_id",
                ),
                message_id=message_id,
                typ="text",
            )
        )

    async def upload_media(
        self,
        media: str | pathlib.Path | bytes | BinaryIO,
        mime_type: str | None = None,
        filename: str | None = None,
        dl_session: httpx.AsyncClient | None = None,
        *,
        phone_id: str | int | None = None,
    ) -> Media:
        """
        Upload media to WhatsApp servers.

        - All media files sent through this endpoint are encrypted and persist for 30 days, unless they are deleted earlier.
        - You can get media URL with :py:func:`~pywa.client.WhatsApp.get_media_url` and download it with :py:func:`~pywa.client.WhatsApp.download_media` or delete it with :py:func:`~pywa.client.WhatsApp.delete_media`.
        - See `Upload media <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#upload-media>`_.
        - See `Supported media types <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types>`_.

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
            dl_session: A httpx client to use when downloading the media from a URL (optional, if not provided, a
             new session will be created).
            phone_id: The phone ID to upload the media to (optional, if not provided, the client's phone ID will be used).

        Returns:
            The media ID.

        Raises:
            ValueError:
                - If provided ``media`` is file path and the file does not exist.
                - If provided ``media`` is URL and the URL is invalid or media cannot be downloaded.
                - If provided ``media`` is bytes and ``filename`` or ``mime_type`` is not provided.
        """
        phone_id = helpers.resolve_arg(
            wa=self,
            value=phone_id,
            method_arg="phone_id",
            client_arg="phone_id",
        )

        if isinstance(media, (str, pathlib.Path)):
            if (path := pathlib.Path(media)).is_file():
                file, filename, mime_type = (
                    open(path, "rb"),
                    filename or path.name,
                    mime_type or mimetypes.guess_type(path)[0],
                )
            elif (url := str(media)).startswith(("https://", "http://")):
                res = await (
                    dl_session or httpx.AsyncClient(follow_redirects=True)
                ).get(url)
                try:
                    res.raise_for_status()
                except httpx.HTTPError as e:
                    raise ValueError(
                        f"An error occurred while downloading from {url}"
                    ) from e
                file, filename, mime_type = (
                    res.content,
                    filename or pathlib.Path(media).name,
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
        return Media(
            _client=self,
            id=(
                await self.api.upload_media(
                    phone_id=phone_id,
                    filename=filename,
                    media=file,
                    mime_type=mime_type,
                )
            )["id"],
        )

    async def get_media_url(self, media_id: str) -> MediaUrlResponse:
        """
        Get a media URL for a media ID.

        - Note that clicking this URL (i.e. performing a generic ``GET``) will not return the media; you must include an access token. Use the :py:func:`~pywa.client.WhatsApp.download_media` method to download the media.
        - The media can be downloaded directly from the message using the :py:func:`~pywa.types.Message.download_media` method.
        - The URL is valid for 5 minutes.
        - See `Retrieve Media URL <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#retrieve-media-url>`_.

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
        path: str | pathlib.Path | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **httpx_kwargs: Any,
    ) -> pathlib.Path | bytes:
        """
        Download a media file from WhatsApp servers.

        - See `Download media <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#download-media>`_.

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
            **httpx_kwargs: Additional arguments to pass to :py:func:`httpx.get`.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.
        """
        content, mimetype = await self.api.get_media_bytes(
            media_url=url, **httpx_kwargs
        )
        if in_memory:
            return content
        if path is None:
            path = pathlib.Path.cwd()
        if filename is None:
            clean_mimetype = mimetype.split(";")[0].strip() if mimetype else None
            filename = hashlib.sha256(url.encode()).hexdigest() + (
                (mimetypes.guess_extension(clean_mimetype) if clean_mimetype else None)
                or ".bin"
            )
        path = pathlib.Path(path) / filename
        with open(path, "wb") as f:
            f.write(content)
        return path

    async def delete_media(
        self,
        media_id: str,
        *,
        phone_id: str | int | None = utils.MISSING,
    ) -> SuccessResult:
        """
        Delete a media file from WhatsApp servers.

        - See `Delete media <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#delete-media>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.delete_media(media_id='wamid.XXX=')

        Args:
            media_id: The media ID to delete.
            phone_id: The phone ID to delete the media from (optional, If included, the operation will only be processed if the ID matches the ID of the business phone number that the media was uploaded on. pass ``None`` to use the client's phone ID).

        Returns:
            Whether the media was deleted successfully.
        """
        return SuccessResult.from_dict(
            await self.api.delete_media(
                media_id=media_id,
                phone_number_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                )
                if phone_id is not utils.MISSING
                else None,
            )
        )

    async def get_business_account(
        self,
        *,
        waba_id: str | int | None = None,
    ) -> WhatsAppBusinessAccount:
        """
        Get the WhatsApp Business Account (WABA) information.

        Args:
            waba_id: The WABA ID to get the information from (optional, if not provided, the client's WABA ID will be used).

        Returns:
            The WhatsApp Business Account object.
        """
        return WhatsAppBusinessAccount.from_dict(
            data=await self.api.get_waba_info(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                fields=WhatsAppBusinessAccount._api_fields(),
            )
        )

    async def get_business_phone_number(
        self,
        *,
        phone_id: str | int | None = None,
    ) -> BusinessPhoneNumber:
        """
        Get the phone number of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_phone_number()

        Args:
            phone_id: The phone ID to get the phone number from (optional, if not provided, the client's phone ID will be used).

        Returns:
            The phone number object.
        """
        return BusinessPhoneNumber.from_dict(
            data=await self.api.get_business_phone_number(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                fields=BusinessPhoneNumber._api_fields(),
            )
        )

    async def get_business_phone_numbers(
        self,
        *,
        waba_id: str | int | None = None,
        pagination: Pagination | None = None,
    ) -> Result[BusinessPhoneNumber]:
        """
        Get the phone numbers of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_phone_numbers()

        Args:
            waba_id: The WABA ID to get the phone numbers from (optional, if not provided, the client's WABA ID will be used).
            pagination: Pagination object to paginate through the results (optional).

        Returns:
            A Result object containing BusinessPhoneNumber objects.
        """
        return Result(
            wa=self,
            response=await self.api.get_business_phone_numbers(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                pagination=pagination.to_dict() if pagination else None,
                fields=BusinessPhoneNumber._api_fields(),
            ),
            item_factory=BusinessPhoneNumber.from_dict,
        )

    async def get_business_phone_number_settings(
        self,
        *,
        include_sip_credentials: bool | None = None,
        phone_id: str | int | None = None,
    ) -> BusinessPhoneNumberSettings:
        """
        Get the settings of the WhatsApp Business phone number.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_phone_number_settings()

        Args:
            include_sip_credentials: Whether to include SIP credentials in the response (optional, default: False).
            phone_id: The phone ID to get the settings from (optional, if not provided, the client's phone ID will be used).

        Returns:
            The business phone number settings.
        """
        return BusinessPhoneNumberSettings.from_dict(
            data=await self.api.get_business_phone_number_settings(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                fields=BusinessPhoneNumberSettings._api_fields(),
                include_sip_credentials=include_sip_credentials,
            )
        )

    async def update_business_phone_number_settings(
        self,
        settings: BusinessPhoneNumberSettings,
        *,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Update the settings of the WhatsApp Business phone number.

        Example:

            >>> from pywa_async.types.calls import CallingSettingsStatus
            >>> wa = WhatsApp(...)
            >>> s = await wa.get_business_phone_number_settings()
            >>> s.calling.status = CallingSettingsStatus.ENABLED
            >>> wa.update_business_phone_number_settings(settings)

        Args:
            settings: The new settings to update.
            phone_id: The phone ID to update the settings for (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the settings were updated successfully.
        """
        return SuccessResult.from_dict(
            await self.api.update_business_phone_number_settings(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                settings=settings.to_dict(),
            )
        )

    async def update_conversational_automation(
        self,
        enable_chat_opened: bool,
        ice_breakers: Iterable[str] | None = None,
        commands: Iterable[Command] | None = None,
        *,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
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
            phone_id: The phone ID to update the conversational automation settings for (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the conversational automation settings were updated.
        """
        return SuccessResult.from_dict(
            await self.api.update_conversational_automation(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                enable_welcome_message=enable_chat_opened,
                prompts=tuple(ice_breakers) if ice_breakers else None,
                commands=json.dumps([c.to_dict() for c in commands])
                if commands
                else None,
            )
        )

    async def update_display_name(
        self, new_display_name: str, *, phone_id: str | int | None = None
    ) -> SuccessResult:
        """
        Update the display name of the WhatsApp Business account.

        - The display name is the name that appears in the WhatsApp app for your business.
        - The display name will undergo verification by WhatsApp, and you will receive a webhook notification when the verification is complete.
        - Read more about `Display Name Verification <https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers#display-name-verification>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.update_display_name()

        Args:
            new_display_name: The new display name.
            phone_id: The phone ID to update the display name for (optional, if not provided, the client's phone ID will be used).
        """

        return SuccessResult.from_dict(
            await self.api.update_display_name(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                new_display_name=new_display_name,
            )
        )

    async def get_business_profile(
        self,
        *,
        phone_id: str | int | None = None,
    ) -> BusinessProfile:
        """
        Get the business profile of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_business_profile()

        Args:
            phone_id: The phone ID to get the business profile from (optional, if not provided, the client's phone ID will be used).

        Returns:
            The business profile.
        """
        return BusinessProfile.from_dict(
            data=(
                await self.api.get_business_profile(
                    phone_id=helpers.resolve_arg(
                        wa=self,
                        value=phone_id,
                        method_arg="phone_id",
                        client_arg="phone_id",
                    ),
                    fields=BusinessProfile._api_fields(),
                )
            )["data"][0]
        )

    async def set_business_public_key(
        self,
        public_key: str,
        *,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Set the business public key of the WhatsApp Business account (required for end-to-end encryption in flows)

        Args:
            public_key: An public 2048-bit RSA Key in PEM format.
            phone_id: The phone ID to set the business public key for (optional, if not provided, the client's phone ID will be used).

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.set_business_public_key(
            ...     public_key=\"\"\"-----BEGIN PUBLIC KEY-----...\"\"\"
            ... )


        Returns:
            Whether the business public key was set.
        """
        return SuccessResult.from_dict(
            await self.api.set_business_public_key(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                public_key=public_key,
            )
        )

    async def update_business_profile(
        self,
        about: str | None = utils.MISSING,
        address: str | None = utils.MISSING,
        description: str | None = utils.MISSING,
        email: str | None = utils.MISSING,
        profile_picture_handle: str | None = utils.MISSING,
        industry: Industry | None = utils.MISSING,
        websites: Iterable[str] | None = utils.MISSING,
        *,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Update the business profile of the WhatsApp Business account.

        Example:

            >>> from pywa.types import Industry
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
            phone_id: The phone ID to update the business profile for (optional, if not provided, the client's phone ID will be used).

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
            if value is not utils.MISSING
        }
        return SuccessResult.from_dict(
            await self.api.update_business_profile(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                data=data,
            )
        )

    async def get_commerce_settings(
        self,
        *,
        phone_id: str | int | None = None,
    ) -> CommerceSettings:
        """
        Get the commerce settings of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.get_commerce_settings()

        Returns:
            The commerce settings.
        """
        return CommerceSettings.from_dict(
            data=(
                await self.api.get_commerce_settings(
                    phone_id=helpers.resolve_arg(
                        wa=self,
                        value=phone_id,
                        method_arg="phone_id",
                        client_arg="phone_id",
                    ),
                    fields=CommerceSettings._api_fields(),
                )
            )["data"][0]
        )

    async def update_commerce_settings(
        self,
        is_catalog_visible: bool = None,
        is_cart_enabled: bool = None,
        *,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
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
            phone_id: The phone ID to update the commerce settings for (optional, if not provided, the client's phone ID will be used).

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
        return SuccessResult.from_dict(
            await self.api.update_commerce_settings(
                phone_id=helpers.resolve_arg(
                    wa=self,
                    value=phone_id,
                    method_arg="phone_id",
                    client_arg="phone_id",
                ),
                data=data,
            )
        )

    async def create_template(
        self,
        template: Template | LibraryTemplate,
        *,
        waba_id: str | int | None = None,
        app_id: str | int | None = None,
    ) -> CreatedTemplate:
        """
        Create a template for the WhatsApp Business account.

        - WhatsApp Business Accounts can only create 100 message templates per hour.
        - Read more about `Create and Manage Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#create-and-manage-templates>`_.

        Example::

            from pywa.types import template as t

            wa = WhatsApp(..., business_account_id='1234567890')

            created = wa.create_template(
                template=t.Template(
                    name='seasonal_promotion',
                    category=t.TemplateCategory.MARKETING,
                    language=t.TemplateLanguage.ENGLISH_US,
                    parameter_format=t.ParamFormat.NAMED,
                    components=[
                        t.HeaderText(text='Our {{sale_name}} is on!', sale_name='Summer Sale'),
                        t.BodyText(
                            text='Shop now through {{end_date}} and use code {{discount_code}} to get {{discount_amount}} off of all merchandise.',
                            end_date='the end of August', discount_code='25OFF', discount_amount='25%'
                        ),
                        t.FooterText(text='Use the buttons below to manage your marketing subscriptions'),
                        t.Buttons(
                            buttons=[
                                t.QuickReplyButton(text='Unsubscribe from Promos'),
                                t.QuickReplyButton(text='Unsubscribe from All'),
                            ]
                        ),
                    ],
                ),

                print('Template created:', created.id, created.status)

        Args:
            template: The template to create.
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID, optional).
            app_id: The App ID to upload the template header example media to (optional, if not provided, the client's app ID will be used).

        Returns:
            The created template.
        """
        if isinstance(template, Template):
            await helpers.upload_template_media_components(
                wa=self, app_id=app_id, components=template.components
            )
        return CreatedTemplate.from_dict(
            client=self,
            data=await self.api.create_template(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                template=json.loads(template.to_json()),
            ),
        )

    async def upsert_authentication_template(
        self,
        *,
        name: str,
        languages: Iterable[TemplateLanguage],
        otp_button: BaseOTPButton,
        add_security_recommendation: bool | None = None,
        code_expiration_minutes: int | None = None,
        message_send_ttl_seconds: int | None = None,
        waba_id: str | int | None = None,
    ) -> CreatedTemplates:
        """
        Bulk update or create authentication templates in multiple languages that include or exclude the optional security and expiration warnings.

        - If a template already exists with a matching name and language, the template will be updated with the contents of the request, otherwise, a new template will be created.
        - You can't provide the ``text`` or ``autofill_text`` properties for the OTP Buttons. It will be automatically set to a pre-set value localized to the template's language. For example, `Copy Code` for English (US) and `Autofill` for English (US).
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates#bulk-management>`_.
        - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/authentication-templates>`_.


        Example:

            >>> from pywa.types.templates import *
            >>> wa = WhatsApp(...)
            >>> templates = await wa.upsert_authentication_template(
            ...     name='one_tap_authentication',
            ...     languages=[TemplateLanguage.ENGLISH_US, TemplateLanguage.FRENCH, TemplateLanguage.SPANISH],
            ...     otp_button=OneTapOTPButton(supported_apps=...),
            ...     add_security_recommendation=True,
            ...     code_expiration_minutes=5,
            ... )
            ... for template in templates:
            ...     print(f'Template {template.id} created with status {template.status}')

        Args:
            name: The name of the template (should be unique, maximum 512 characters).
            languages: A list of languages and locale codes to create or update the template in (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
            otp_button: A :class:`OneTapOTPButton`, :class:`ZeroTapOTPButton`, or :class:`CopyCodeOTPButton` button.
            add_security_recommendation: Boolean value to add information to the template about not sharing authentication codes with anyone.
            code_expiration_minutes: Integer value to add information to the template on when the code will expire.
            message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds. (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID, optional).

        Returns:
            A :class:`CreatedTemplates` object containing the created or updated templates.
        """
        return CreatedTemplates.from_dict(
            data=await self.api.upsert_message_templates(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                template=json.loads(
                    _AuthenticationTemplates(
                        name=name,
                        languages=list(languages),
                        components=[
                            AuthenticationBody(
                                add_security_recommendation=add_security_recommendation
                            ),
                            AuthenticationFooter(
                                code_expiration_minutes=code_expiration_minutes
                            ),
                            Buttons(buttons=[otp_button]),
                        ],
                    ).to_json()
                ),
            ),
            client=self,
        )

    async def send_template(
        self,
        to: str | int,
        name: str,
        language: TemplateLanguage,
        params: list[TemplateBaseComponent.Params | dict] | None = None,
        *,
        use_mm_lite_api: bool = False,
        message_activity_sharing: bool | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentTemplate:
        """
        Send a template to a WhatsApp user.

        - To create a template, use :py:func:`~pywa.client.WhatsApp.create_template`.
        - Read more about `Template Messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates>`_.

        Example::

            from pywa.types.templates import *

            wa = WhatsApp(...)
            wa.send_template(
                to='1234567890',
                name='seasonal_promotion',
                language=TemplateLanguage.ENGLISH_US,
                params=[
                    BodyText.Params(text='Our {{season}} sale is on!', season='Summer'),
                    CopyCodeButton.Params(coupon_code="25OFF", index=0)
                ],
            )

            from pywa.types.templates import *

            t = Template(
                name='seasonal_promotion',
                category=TemplateCategory.MARKETING,
                language=TemplateLanguage.ENGLISH_US,
                parameter_format=ParamFormat.NAMED,
                components=[
                    header := HeaderText(text='Our {{sale_name}} is on!', sale_name='Summer Sale'),
                    body := BodyText(
                        text='Shop now through {{end_date}} and use code {{discount_code}} to get {{discount_amount}} off of all merchandise.',
                        end_date='the end of August', discount_code='25OFF', discount_amount='25%'
                    ),
                    FooterText(text='Use the buttons below to manage your marketing subscriptions'),
                    Buttons(
                        buttons=[
                            uns_from_promos := QuickReplyButton(text='Unsubscribe from Promos'),
                            uns_from_all := QuickReplyButton(text='Unsubscribe from All'),
                        ]
                    ),
                ],
            )

            wa.create_template(template=t)

            wa.send_template(
                to='1234567890',
                name=t.name,
                language=t.language,
                params=[
                    header.params(sale_name='Summer Sale'),
                    body.params(
                        end_date='the end of August',
                        discount_code='25OFF',
                        discount_amount='25%',
                    ),
                    uns_from_promos.params(callback_data='uns_from_promos'),
                    uns_from_all.params(callback_data='uns_from_all'),
                ],
            )

        Args:
            to: The phone ID of the WhatsApp user.
            name: The name of the template to send.
            language: The language of the template to send.
            params: The parameters to fill in the template.
            use_mm_lite_api: Whether to use `Marketing Messages Lite API <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api>`_ (optional, default: False).
            message_activity_sharing: Whether to share message activities (e.g. message read) for that specific marketing message to Meta to help optimize marketing messages (optional, only if ``use_mm_lite_api`` is True).
            reply_to_message_id: The ID of the message to reply to (optional).
            tracker: A callback data to track the message (optional, can be a string or a :class:`CallbackData` object).
            sender: The phone ID to send the template from (optional, if not provided, the client's phone ID will be used).
        """
        sender = helpers.resolve_arg(
            wa=self, value=sender, method_arg="sender", client_arg="phone_id"
        )
        if params is not None:
            await helpers.upload_template_media_params(
                wa=self,
                sender=sender,
                params=params,
            )
        template = {
            "name": name,
            "language": {"code": language.value},
            **(
                {
                    "components": [
                        param.to_dict()
                        if isinstance(param, TemplateBaseComponent.Params)
                        else param
                        for param in params
                    ]
                }
                if params is not None
                else {}
            ),
        }
        return SentTemplate.from_sent_update(
            client=self,
            update=await self.api.send_message(
                sender=sender,
                to=str(to),
                typ="template",
                msg=template,
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            )
            if not use_mm_lite_api
            else await self.api.send_marketing_message(
                sender=sender,
                to=str(to),
                template=template,
                message_activity_sharing=message_activity_sharing,
                reply_to_message_id=reply_to_message_id,
                biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
            ),
            from_phone_id=sender,
        )

    async def get_templates(
        self,
        *,
        statuses: Iterable[TemplateStatus] | None = None,
        categories: Iterable[TemplateCategory] | None = None,
        languages: Iterable[TemplateLanguage] | None = None,
        name: str | None = None,
        content: str | None = None,
        name_or_content: str | None = None,
        quality_scores: Iterable[QualityScoreType] | None = None,
        pagination: Pagination | None = None,
        waba_id: str | int | None = None,
    ) -> TemplatesResult:
        """
        Get templates of the WhatsApp Business account.

        Example:

            >>> wa = WhatsApp(...)
            >>> templates = wa.get_templates(
            ...     statuses=[TemplateStatus.APPROVED],
            ...     categories=[TemplateCategory.MARKETING],
            ...     languages=[TemplateLanguage.ENGLISH_US],
            ...     pagination=Pagination(limit=10)
            ... )

        Args:
            statuses: The statuses of the templates to filter by (optional).
            categories: The categories of the templates to filter by (optional).
            languages: The languages of the templates to filter by (optional).
            name: The name (or part of it) of the template to filter by (optional).
            content: The content of the template to filter by (optional).
            name_or_content: The name or content of the template to filter by (optional).
            quality_scores: The quality scores of the templates to filter by (optional).
            pagination: Pagination parameters (optional).
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID, optional).

        Returns:
            A Result object containing the templates
        """
        return TemplatesResult(
            wa=self,
            response=await self.api.get_templates(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                fields=TemplateDetails._api_fields(),
                filters={
                    k: v
                    for k, v in {
                        "status": ",".join(statuses) if statuses else None,
                        "category": ",".join(categories) if categories else None,
                        "language": ",".join(languages) if languages else None,
                        "name": name,
                        "content": content,
                        "name_or_content": name_or_content,
                        "quality_score": ",".join(quality_scores)
                        if quality_scores
                        else None,
                    }.items()
                    if v is not None
                },
                summary_fields=(
                    "total_count",
                    "message_template_count",
                    "message_template_limit",
                    "are_translations_complete",
                ),
                pagination=pagination.to_dict() if pagination else None,
            ),
            item_factory=functools.partial(
                TemplateDetails.from_dict,
                client=self,
            ),
        )

    async def get_template(self, template_id: int | str) -> TemplateDetails:
        """
        Get the details of a specific template.

        Args:
            template_id: The ID of the template to retrieve.

        Returns:
            A TemplateDetails object containing the template details.
        """
        return TemplateDetails.from_dict(
            data=await self.api.get_template(
                template_id=str(template_id),
                fields=TemplateDetails._api_fields(),
            ),
            client=self,
        )

    async def update_template(
        self,
        template_id: int | str,
        *,
        new_category: TemplateCategory | None = None,
        new_components: list[TemplateBaseComponent] | None = None,
        new_message_send_ttl_seconds: int | None = None,
        new_parameter_format: ParamFormat | None = None,
        app_id: str | int | None = None,
    ) -> UpdatedTemplate:
        """
        Update an existing template.

        - Only templates with an ``APPROVED``, ``REJECTED``, or ``PAUSED`` status can be edited.
        - You cannot edit the category of an approved template.
        - Approved templates can be edited up to 10 times in a 30 day window, or 1 time in a 24 hour window. Rejected or paused templates can be edited an unlimited number of times.
        - After editing an approved or paused template, it will automatically be approved unless it fails template review.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#edit-a-message-template>`_.

        Args:
            template_id: The ID of the template to update.
            new_category: The new category of the template (optional, cannot be changed for approved templates).
            new_components: The new components of the template (optional, if not provided, the existing components will be used).
            new_message_send_ttl_seconds: The new message send TTL in seconds (optional, if not provided, the existing TTL will be used).
            new_parameter_format: The new parameter format (optional, if not provided, the existing format will be used).
            app_id: The App ID to upload the template header example media to (optional, if not provided, the client's app ID will be used).

        Returns:
            Whether the template was updated successfully.
        """
        if new_components:
            await helpers.upload_template_media_components(
                wa=self,
                app_id=app_id,
                components=new_components,
            )
        return UpdatedTemplate.from_dict(
            data=await self.api.update_template(
                template_id=template_id,
                template=json.loads(
                    _TemplateUpdate(
                        category=new_category,
                        components=new_components,
                        message_send_ttl_seconds=new_message_send_ttl_seconds,
                        parameter_format=new_parameter_format,
                    ).to_json()
                ),
            ),
            client=self,
        )

    async def delete_template(
        self,
        template_name: str,
        *,
        template_id: int | str | None = None,
        waba_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Delete a template.

        - If you delete a template that has been sent in a template message but has yet to be delivered (e.g. because the customer's phone is turned off), the template's status will be set to PENDING_DELETION and we will attempt to deliver the message for 30 days. After this time you will receive a "Structure Unavailable" error and the customer will not receive the message.
        - Names of an approved template that has been deleted cannot be used again for 30 days.
        - Deleting a template by name deletes all templates that match that name (meaning templates with the same name but different languages will also be deleted).
        - To delete a template by ID, include the template's ID along with its name in your request; only the template with the matching template ID will be deleted.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#deleting-templates>`_.

        Args:
            template_name: The name of the template to delete.
            template_id: The ID of the template to delete (optional, if provided, only the template with the matching ID will be deleted).
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID, optional).

        Returns:
            Whether the template was deleted successfully.
        """
        return SuccessResult.from_dict(
            await self.api.delete_template(
                waba_id=helpers.resolve_arg(
                    wa=self,
                    value=waba_id,
                    method_arg="waba_id",
                    client_arg="business_account_id",
                ),
                template_name=template_name,
                template_id=template_id,
            )
        )

    async def compare_templates(
        self,
        template_id: int | str,
        *template_ids: int | str,
        start: datetime.datetime | int,
        end: datetime.datetime | int,
    ) -> TemplatesCompareResult:
        """
        You can compare two templates by examining how often each one is sent, which one has the lower ratio of blocks to sends, and each template's top reason for being blocked.

        - Only two templates can be compared at a time.
        - Both templates must be in the same WhatsApp Business Account.
        - Templates must have been sent at least 1,000 times in the queries specified timeframe.
        - Timeframes are limited to ``7``, ``30``, ``60`` and ``90`` day lookbacks from the time of the request.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-comparison>`_.

        Args:
            template_id: The ID of the template to compare against others.
            template_ids: The IDs of the templates to compare with the given template.
            start: The start date of the comparison period.
            end: The end date of the comparison period.

        Returns:
            A TemplatesCompareResult object containing the comparison results.
        """
        if not template_ids:
            raise ValueError(
                "At least one template ID must be provided for comparison."
            )
        return TemplatesCompareResult.from_dict(
            data=await self.api.compare_templates(
                template_id=template_id,
                template_ids=tuple(map(str, template_ids)),
                start=str(
                    int(start.timestamp())
                    if isinstance(start, datetime.datetime)
                    else start
                ),
                end=str(
                    int(end.timestamp()) if isinstance(end, datetime.datetime) else end
                ),
            )
        )

    async def migrate_templates(
        self,
        source_waba_id: str | int,
        page_number: int | None = None,
        *,
        destination_waba_id: str | int | None = None,
    ) -> MigrateTemplatesResult:
        """
        Migrate templates from one WhatsApp Business account to another.

        - Templates can only be migrated between WABAs owned by the same Meta business.
        - Only templates with a status of ``APPROVED`` and a quality_score of either ``GREEN`` or ``UNKNOWN`` are eligible for migration.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-migration>`_.

        Args:
            source_waba_id: The WhatsApp Business account ID to migrate templates from.
            page_number: Indicates amount of templates to migrate as sets of 500. Zero-indexed. For example, to migrate 1000 templates, send one request with this value set to 0 and another request with this value set to 1, in parallel.
            destination_waba_id: The WhatsApp Business account ID to migrate templates to (optional, overrides the client's business account ID).

        Returns:
            A MigrateTemplatesResult object containing the migration results.
        """
        return MigrateTemplatesResult.from_dict(
            data=await self.api.migrate_templates(
                source_waba_id=str(source_waba_id),
                dest_waba_id=helpers.resolve_arg(
                    wa=self,
                    value=destination_waba_id,
                    method_arg="destination_waba_id",
                    client_arg="business_account_id",
                ),
                page_number=page_number,
            )
        )

    async def unpause_template(
        self,
        template_id: int | str,
    ) -> TemplateUnpauseResult:
        """
        Unpause a template that has been paused due to pacing.

        - You must wait 5 minutes after a template has been paused as a result of pacing before calling this method.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#unpausing>`_.

        Args:
            template_id: The ID of the template to unpause.

        Returns:
            A TemplateUnpauseResult object containing the result of the unpause operation.
        """
        res = await self.api.unpause_template(str(template_id))
        return TemplateUnpauseResult(
            success=res["success"],
            reason=res.get("reason"),
        )

    # fmt: off
    async def create_flow(
        self,
        name: str,
        categories: Iterable[FlowCategory | str],
        *,
        clone_flow_id: str | None = None,
        endpoint_uri: str | None = None,
        flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO | None = None,
        publish: bool | None = None,
        waba_id: str | int | None = None,
    ) -> CreatedFlow:
        """
        Create a flow.

        - This method requires the WhatsApp Business account ID to be provided when initializing the client.
        - New Flows are created in :class:`FlowStatus.DRAFT` status unless ``flow_json`` is provided and ``publish`` is True.
        - To update the flow json, use :py:func:`~pywa.client.WhatsApp.update_flow`.
        - To send a flow, use :py:func:`~pywa.client.WhatsApp.send_flow`.

        Args:
            name: The name of the flow (must be unique, can be used later to update and send the flow).
            categories: The categories of the flow.
            flow_json: The JSON of the flow (optional, if provided, the flow will be created with the provided JSON).
            publish: Whether to publish the flow after creating it, only works if ``flow_json`` is provided.
            clone_flow_id: The flow ID to clone (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from Flow 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a Flow with version below 3.0.
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID).

        Example:

            >>> from pywa.types.flows import *
            >>> wa = WhatsApp(...)
            >>> wa.create_flow(
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER],
            ...     flow_json=FlowJSON(...),
            ...     publish=True,
            ... )

        Returns:
            The created flow.

        Raises:
            FlowBlockedByIntegrity: If you can't create a flow because of integrity issues.
        """
        return CreatedFlow.from_dict(
            await self.api.create_flow(
                name=name,
                categories=tuple(map(str, categories)),
                clone_flow_id=clone_flow_id,
                endpoint_uri=endpoint_uri,
                waba_id=helpers.resolve_arg(wa=self, value=waba_id, method_arg="waba_id", client_arg="business_account_id"),
                flow_json=helpers.resolve_flow_json_param(flow_json)
                if flow_json
                else None,
                publish=publish,
            )
        )

    async def update_flow_metadata(
        self,
        flow_id: str | int,
        *,
        name: str | None = None,
        categories: Iterable[FlowCategory | str] | None = None,
        endpoint_uri: str | None = None,
        application_id: int | None = None,
    ) -> SuccessResult:
        """
        Update the metadata of a flow.

        Args:
            flow_id: The flow ID.
            name: The name of the flow (optional).
            categories: The new categories of the flow (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from FlowJSON 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a FlowJSON with version below 3.0.
            application_id: The ID of the Meta application which will be connected to the Flow. All the flows with endpoints need to have an Application connected to them.

        Example:

            >>> from pywa_async.types.flows import FlowCategory
            >>> wa = WhatsApp(...)
            >>> wa.update_flow_metadata(
            ...     flow_id='1234567890',
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER],
            ...     endpoint_uri='https://my-api-server/feedback_flow',
            ...     application_id=1234567890,
            ... )

        Returns:
            Whether the flow was updated.

        Raises:
            ValueError: If neither of the arguments is provided.
        """
        if not any((name, categories, endpoint_uri, application_id)):
            raise ValueError("At least one argument must be provided")
        return SuccessResult.from_dict(
            await self.api.update_flow_metadata(
                flow_id=str(flow_id),
                name=name,
                categories=tuple(map(str, categories)) if categories else None,
                endpoint_uri=endpoint_uri,
                application_id=application_id,
            )
        )

    async def update_flow_json(
        self,
        flow_id: str | int,
        flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO,
    ) -> FlowJSONUpdateResult:
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
        return FlowJSONUpdateResult.from_dict(
            await self.api.update_flow_json(flow_id=str(flow_id), flow_json=helpers.resolve_flow_json_param(flow_json)))

    async def publish_flow(
        self,
        flow_id: str | int,
    ) -> SuccessResult:
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
        return SuccessResult.from_dict(await self.api.publish_flow(flow_id=str(flow_id)))

    async def delete_flow(
        self,
        flow_id: str | int,
    ) -> SuccessResult:
        """
        While a Flow is in DRAFT status, it can be deleted.

        Args:
            flow_id: The flow ID.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If the flow is already published.
        """
        return SuccessResult.from_dict(await self.api.delete_flow(flow_id=str(flow_id)))

    async def deprecate_flow(
        self,
        flow_id: str | int,
    ) -> SuccessResult:
        """
        Once a Flow is published, it cannot be modified or deleted, but can be marked as deprecated.

        Args:
            flow_id: The flow ID.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If the flow is not published or already deprecated.
        """
        return SuccessResult.from_dict(await self.api.deprecate_flow(flow_id=str(flow_id)))

    async def get_flow(
            self,
            flow_id: str | int,
            *,
            invalidate_preview: bool = True,
            phone_number_id: str | int | None = None,
    ) -> FlowDetails:
        """
        Get the details of a flow.

        Args:
            flow_id: The flow ID.
            invalidate_preview: Whether to invalidate the preview (optional, default: True).
            phone_number_id: To check that a flow can be used with a specific phone number (optional).

        Returns:
            The details of the flow.
        """
        return FlowDetails.from_dict(
            data=(
                await self.api.get_flow(
                    flow_id=str(flow_id),
                    fields=FlowDetails._api_fields(
                        invalidate_preview=invalidate_preview,
                        phone_number_id=phone_number_id,
                    ),
                )
            ),
            client=self,
        )

    async def get_flows(
            self,
            *,
            invalidate_preview: bool = True,
            phone_number_id: str | int | None = None,
            pagination: Pagination | None = None,
            waba_id: str | int | None = None,
    ) -> Result[FlowDetails]:
        """
        Get the flows associated with the WhatsApp Business account.

        - This method requires the WhatsApp Business account ID to be provided when initializing the client.

        Args:
            invalidate_preview: Whether to invalidate the preview (optional, default: True).
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID).
            phone_number_id: To check that the flows can be used with a specific phone number (optional).
            pagination: The pagination parameters (optional).

        Returns:
            Result object containing the flows.
        """
        return Result(
            wa=self,
            response=await self.api.get_flows(
                waba_id=helpers.resolve_arg(wa=self, value=waba_id, method_arg="waba_id", client_arg="business_account_id"),
                fields=FlowDetails._api_fields(
                    invalidate_preview=invalidate_preview,
                    phone_number_id=phone_number_id,
                ),
                pagination=pagination.to_dict() if pagination else None,
            ),
            item_factory=functools.partial(FlowDetails.from_dict, client=self),
        )

    async def get_flow_metrics(
        self,
        flow_id: str | int,
        metric_name: FlowMetricName,
        granularity: FlowMetricGranularity,
            *,
        since: datetime.date | str | None = None,
        until: datetime.date | str | None = None,
    ) -> dict:
        """
        Get the metrics of a flow.

        Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/metrics_api>`_.

        Args:
            flow_id: The flow ID.
            metric_name: See `Available Metrics <https://developers.facebook.com/docs/whatsapp/flows/reference/metrics_api#available_metrics>`_.
            granularity: Time granularity.
            since: Start of the time period. If not specified, the oldest allowed date will be used. Oldest allowed date depends on the specified time granularity: DAY - 90 days, HOUR - 30 days.
            until: End of the time period. If not specified, the current date will be used.

        Returns:

        """
        return (
            await self.api.get_flow(
                flow_id=str(flow_id),
                fields=(
                    helpers.get_flow_metric_field(
                        metric_name=metric_name,
                        granularity=granularity,
                        since=since,
                        until=until,
                    ),
                ),
            )
        )["metric"]

    async def get_flow_assets(
        self,
        flow_id: str | int,
        *,
        pagination: Pagination | None = None,
    ) -> Result[FlowAsset]:
        """
        Get assets attached to a specified Flow.

        Args:
            flow_id: The flow ID.
            pagination: The pagination parameters (optional).

        Returns:
            Result object containing the assets of the flow.
        """
        return Result(
            wa=self,
            response=await self.api.get_flow_assets(
                flow_id=str(flow_id),
                pagination=pagination.to_dict() if pagination else None,
            ),
            item_factory=FlowAsset.from_dict,
        )

    async def migrate_flows(
            self,
            source_waba_id: str | int,
            source_flow_names: Iterable[str],
            *,
            destination_waba_id: str | int | None = None,
    ) -> MigrateFlowsResponse:
        """
        Migrate flows from one WhatsApp Business Account to another.

        Args:
            source_waba_id: The source WhatsApp Business Account ID.
            source_flow_names: The names of the flows to migrate.
            destination_waba_id: The destination WhatsApp Business Account ID (optional, if not provided, the client's business account ID will be used).

        Returns:
            The response of the migration request.
        """
        return MigrateFlowsResponse.from_dict(
            await self.api.migrate_flows(
                dest_waba_id=helpers.resolve_arg(
                    wa=self,
                    value=destination_waba_id,
                    method_arg="destination_waba_id",
                    client_arg="business_account_id",
                ),                source_waba_id=str(source_waba_id),
                source_flow_names=tuple(source_flow_names),
            )
        )

    async def register_phone_number(
        self,
        pin: int | str,
            *,

            data_localization_region: str | None = None,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
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
            phone_id: The phone ID to register (optional, if not provided, the client's phone ID will be used).

        Returns:
            The success of the registration.
        """
        return SuccessResult.from_dict(
            await self.api.register_phone_number(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                pin=str(pin),
                data_localization_region=data_localization_region,
            )
        )

    async def deregister_phone_number(
            self,
            *,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Deregister a Business Phone Number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/registration/#deregister>`_

        Args:
            phone_id: The phone ID to deregister (optional, if not provided, the client's phone ID will be used).

        Returns:
            The success of the deregistration.
        """
        return SuccessResult.from_dict(await self.api.deregister_phone_number(
            phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
        ))

    async def create_qr_code(
        self,
        prefilled_message: str,
        image_type: Literal["PNG", "SVG"] = "PNG",
        *,
        phone_id: str | int | None = None,
    ) -> QRCode:
        """
        Create a QR code for a prefilled message.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/qr-code>`_

        Args:
            prefilled_message: The prefilled message.
            image_type: The type of the image (``PNG`` or ``SVG``. default: ``PNG``).
            phone_id: The phone ID to create the QR code for (optional, if not provided, the client's phone ID will be used).

        Returns:
            The QR code.
        """
        return QRCode.from_dict(
            await self.api.create_qr_code(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                prefilled_message=prefilled_message,
                generate_qr_image=image_type,
            )
        )

    async def get_qr_code(
        self,
            code: str,
            *,
            image_type: Literal["PNG", "SVG"] | None = None,
            phone_id: str | int | None = None,
    ) -> QRCode | None:
        """
        Get a QR code.

        Args:
            code: The QR code.
            image_type: The type of the image. if not provided, the image URL will not be returned (faster response).
            phone_id: The phone ID to get the QR code for (optional, if not provided, the client's phone ID will be used).

        Returns:
            The QR code if found, otherwise None.
        """
        qrs = (
            await self.api.get_qr_code(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                code=code,
                fields=QRCode._api_fields(image_type)
            )
        )["data"]
        return QRCode.from_dict(qrs[0]) if qrs else None

    async def get_qr_codes(
            self,
            *,
            image_type: Literal["PNG", "SVG"] | None = None,
            phone_id: str | int | None = None,
            pagination: Pagination | None = None,
    ) -> Result[QRCode]:
        """
        Get QR codes associated with the WhatsApp Phone Number.

        Args:
            image_type: The type of the image. If not provided, the image URL will not be returned (faster response).
            phone_id: The phone ID to get the QR codes for (optional, if not provided, the client's phone ID will be used).
            pagination: The pagination parameters (optional).

        Returns:
            Result object containing the QR codes.
        """
        return Result(
            wa=self,
            response=await self.api.get_qr_codes(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                fields=QRCode._api_fields(image_type),
                pagination=pagination.to_dict() if pagination else None,
            ),
            item_factory=QRCode.from_dict,
        )

    async def update_qr_code(
            self,
            code: str,
            prefilled_message: str,
            *,
            phone_id: str | int | None = None,
    ) -> QRCode:
        """
        Update a QR code.

        Args:
            code: The QR code.
            prefilled_message: The prefilled message.
            phone_id: The phone ID to update the QR code for (optional, if not provided, the client's phone ID will be used).

        Returns:
            The updated QR code.
        """
        return QRCode.from_dict(
            await self.api.update_qr_code(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                code=code,
                prefilled_message=prefilled_message,
            )
        )

    async def delete_qr_code(
        self,
        code: str,*,
        phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Delete a QR code.

        Args:
            code: The QR code.
            phone_id: The phone ID to delete the QR code for (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the QR code was deleted.
        """
        return SuccessResult.from_dict(
            await self.api.delete_qr_code(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                code=code,
            )
        )

    async def get_app_access_token(self, app_id: int, app_secret: str) -> str:
        """
        Get an access token for an app.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/facebook-login/guides/access-tokens/#apptokens>`_.

        Args:
            app_id: The ID of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
            app_secret: The app secret.

        Returns:
            The access token.
        """
        return (
            await self.api.get_app_access_token(
                app_id=app_id,
                app_secret=app_secret,
            )
        )["access_token"]

    async def set_app_callback_url(
        self,
        app_id: int,
        app_access_token: str,
        callback_url: str,
        verify_token: str,
        fields: Iterable[str],
    ) -> SuccessResult:
        """
        Set the callback URL for the webhook.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/reference/app/subscriptions>`_.

        Args:
            app_id: The ID of the app in the
             `App Basic Settings <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings>`_
            app_access_token: The app access token from :meth:`~pywa.client.WhatsApp.get_app_access_token`.
            callback_url: The URL to receive the webhook.
            verify_token: The token to verify the webhook.
            fields: The fields to subscribe to. See `Available Fields <https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-whatsapp#available-subscription-fields>`_.

        Returns:
            Whether the callback URL was set.
        """
        return SuccessResult.from_dict(
            await self.api.set_app_callback_url(
                app_id=app_id,
                app_access_token=app_access_token,
                callback_url=callback_url,
                verify_token=verify_token,
                fields=tuple(fields),
            )
        )

    async def override_waba_callback_url(
        self, callback_url: str, verify_token: str, *,waba_id: str | int | None = None
    ) -> SuccessResult:
        """
        Override the callback URL for the WhatsApp Business account.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-waba-alternate-callback>`_.

        Args:
            callback_url: The URL to receive the webhook.
            verify_token: The token to verify the webhook.
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID).

        Returns:
            Whether the callback URL was overridden.
        """
        return SuccessResult.from_dict(
            await self.api.set_waba_alternate_callback_url(
                waba_id=helpers.resolve_arg(wa=self, value=waba_id, method_arg="waba_id", client_arg="business_account_id"),
                callback_url=callback_url,
                verify_token=verify_token,
            )
        )

    async def delete_waba_callback_url(self, *,waba_id: str | int | None = None) -> SuccessResult:
        """
        Delete the callback URL for the WhatsApp Business account.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#delete-waba-alternate-callback>`_.

        Args:
            waba_id: The WhatsApp Business account ID (Overrides the client's business account ID).

        Returns:
            Whether the callback URL was deleted.
        """
        return SuccessResult.from_dict(
            await self.api.delete_waba_alternate_callback_url(
                waba_id=helpers.resolve_arg(wa=self, value=waba_id, method_arg="waba_id", client_arg="business_account_id"),
            )
        )

    async def override_phone_callback_url(
        self, callback_url: str, verify_token: str, *,phone_id: str | int | None = None
    ) -> SuccessResult:
        """
        Override the callback URL for the phone.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-phone-number-alternate-callback>`_.
        - To access to the current webhook configuration use :meth:`~pywa.client.WhatsApp.get_business_phone_number` and access the ``webhook_configuration`` attribute.

        Args:
            callback_url: The URL to receive the webhook.
            verify_token: The token to verify the webhook.
            phone_id: The phone ID to override the callback URL for (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the callback URL was overridden.
        """
        return SuccessResult.from_dict(
            await self.api.set_phone_alternate_callback_url(
                callback_url=callback_url,
                verify_token=verify_token,
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            )
        )

    async def delete_phone_callback_url(
        self, *,phone_id: str | int | None = None
    ) -> SuccessResult:
        """
        Delete the callback URL for the phone.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#delete-phone-number-alternate-callback>`_.

        Args:
            phone_id: The phone ID to delete the callback URL for (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the callback URL was deleted.
        """
        return SuccessResult.from_dict(
            await self.api.delete_phone_alternate_callback_url(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            )
        )

    async def block_users(
        self, users: Iterable[str | int], *, phone_id: str | int | None = None
    ) -> UsersBlockedResult:
        """
        Block users from sending messages to the WhatsApp Business account.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#unblock-users>`_.
        - You can block users with the :meth:`~pywa.types.others.User.block` or :meth:`~pywa.types.base_update.BaseUserUpdate.block_sender` shortcuts.

        When you block a WhatsApp user, the following happens:

        - The user cannot contact your business or see that you are online.
        - Your business cannot message the user. If you do, you will encounter an error.
        - You can only block users that have messaged your business in the last 24 hours.
        - 64k blocklist limit

        Example:

            >>> wa = WhatsApp(...)
            >>> res = await wa.block_users(users=['1234567890', '0987654321'])
            >>> if res.errors: print(res.failed_users)

        Args:
            users: The phone numbers/wa IDs of the users to block.
            phone_id: The phone ID to block the users from (optional, if not provided, the client's phone ID will be used).

        Returns:
            A UsersBlockedResult object with the status of the block operation.
        """
        return UsersBlockedResult.from_dict(
            data=await self.api.block_users(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                users=tuple(str(phone_id) for phone_id in users),
            ),
            client=self,
        )

    async def unblock_users(
        self, users: Iterable[str | int], *, phone_id: str | int | None = None
    ) -> UsersUnblockedResult:
        """
        Unblock users that were previously blocked from sending messages to the WhatsApp Business account.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#unblock-users>`_.

        Example:
            >>> wa = WhatsApp(...)
            >>> res = await wa.unblock_users(users=['1234567890', '0987654321'])
            >>> print(res.removed_users)

        Args:
            users: The phone numbers/wa IDs of the users to unblock.
            phone_id: The phone ID to unblock the users from (optional, if not provided, the client's phone ID will be used).

        Returns:
            A UsersUnblockedResult object with the status of the unblock operation.
        """
        return UsersUnblockedResult.from_dict(
            data=await self.api.unblock_users(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                users=tuple(str(phone_id) for phone_id in users),
            ),
            client=self,
        )

    async def get_blocked_users(
        self,
        *,
        pagination: Pagination | None = None,
        phone_id: str | int | None = None,
    ) -> Result[User]:
        """
        Get blocked users.

        Example:

            >>> wa = WhatsApp(...)
            >>> for user in await wa.get_blocked_users(): print(user)

        Args:
            pagination: The pagination parameters (optional).
            phone_id: The phone ID to get the list of blocked users from (optional, if not provided, the client's phone ID will be used).

        Returns:
            A Result object with the list of blocked users. You can iterate over the result to get the users.
        """
        return Result(
            wa=self,
            response=await self.api.get_blocked_users(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
                pagination=pagination.to_dict() if pagination else None,
            ),
            item_factory=functools.partial(self._usr_cls.from_dict, client=self)
        )

    async def get_call_permissions(
            self,
            wa_id: str | int,
            *,
            phone_id: str | int | None = None,
    ) -> CallPermissions:
        """
        Get the call permissions for the WhatsApp Business account.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-call-permissions>`_.

        Args:
            wa_id: The WhatsApp ID of the user to get the call permissions for.
            phone_id: The phone ID to get the call permissions from (optional, if not provided, the client's phone ID will be used).

        Returns:
            The call permissions for the user.
        """
        return CallPermissions.from_dict(
            await self.api.get_call_permissions(
                user_wa_id=str(wa_id),
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            ),
        )

    async def initiate_call(
            self,
            to: str | int,
            sdp: SessionDescription,
            *,
            tracker: str | CallbackData | None = None,
            phone_id: str | int | None = None
    ) -> InitiatedCall:
        """
        Initiate a call to a WhatsApp user.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#initiate-call>`_.

        Args:
            to: The number being called (callee)
            sdp: Contains the session description protocol (SDP) type and description language.
            tracker: The data to track the call with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            phone_id: The phone ID to initiate the call from (optional, if not provided, the client's phone ID will be used).

        Returns:
            An InitiatedCall object containing the details of the initiated call.
        """
        return InitiatedCall.from_sent_update(client=self, update=await self.api.initiate_call(
            phone_id=(from_phone_id := helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id")),
            to=(to_wa_id := str(to)),
            sdp=sdp.to_dict(),
            biz_opaque_callback_data=helpers.resolve_tracker_param(tracker),
        ), from_phone_id=from_phone_id, to_wa_id=to_wa_id)


    async def pre_accept_call(
            self,
            call_id: str,
            sdp: SessionDescription,
            *,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Pre-accept a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#pre-accept-call>`_.

        In essence, when you pre-accept an inbound call, you are allowing the calling media connection to be established before attempting to send call media through the connection.

        When you then call the accept call endpoint, media begins flowing immediately since the connection has already been established

        Pre-accepting calls is recommended because it facilitates faster connection times and avoids `audio clipping issues <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/troubleshooting#audio-clipping-issue-and-solution>`_.

        There is about 30 to 60 seconds after the Call Connect webhook is sent for the business to accept the phone call. If the business does not respond, the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Args:
            call_id: The ID of the call to pre-accept.
            sdp: Contains the session description protocol (SDP) type and description language.
            phone_id: The phone ID to pre-accept the call from (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the call was pre-accepted.
        """
        return SuccessResult.from_dict(await self.api.pre_accept_call(
            phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            call_id=call_id,
            sdp=sdp.to_dict() if sdp else None,
        ))

    async def accept_call(
            self,
            call_id: str,
            sdp: SessionDescription,
            *,
            tracker: str | CallbackData | None = None,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Connect to a call by providing a call agent's SDP.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#accept-call>`_.

        You have about 30 to 60 seconds after the Call Connect Webhook is sent to accept the phone call. If your business does not respond, the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Args:
            call_id: The ID of the call to accept.
            sdp: Contains the session description protocol (SDP) type and description language.
            tracker: The data to track the call with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).
            phone_id: The phone ID to accept the call from (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the call was accepted.
        """
        return SuccessResult.from_dict(await self.api.accept_call(
            phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            call_id=call_id,
            sdp=sdp.to_dict() if sdp else None,
            biz_opaque_callback_data=helpers.resolve_tracker_param(tracker)
        ))

    async def reject_call(
            self,
            call_id: str,
            *,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Reject a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#reject-call>`_.

        You have about 30 to 60 seconds after the Call Connect webhook is sent to accept the phone call. If the business does not respond the call is terminated on the WhatsApp user side with a "Not Answered" notification and a Terminate Webhook is delivered back to you.

        Args:
            call_id: The ID of the call to reject.
            phone_id: The phone ID to reject the call from (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the call was rejected.
        """
        return SuccessResult.from_dict(await self.api.reject_call(
            phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),
            call_id=call_id,
        ))

    async def terminate_call(
            self,
            call_id: str,
            *,
            phone_id: str | int | None = None,
    ) -> SuccessResult:
        """
        Terminate an active call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#terminate-call>`_.

        This must be done even if there is an RTCP BYE packet in the media path. Ending the call this way also ensures pricing is more accurate.
        When the WhatsApp user terminates the call, you do not have to call this endpoint. Once the call is successfully terminated, a Call Terminate Webhook will be sent to you.

        Args:
            call_id: The ID of the call to terminate.
            phone_id: The phone ID to terminate the call from (optional, if not provided, the client's phone ID will be used).

        Returns:
            Whether the call was terminated.
        """
        return SuccessResult.from_dict(
            await self.api.terminate_call(
                phone_id=helpers.resolve_arg(wa=self, value=phone_id, method_arg="phone_id", client_arg="phone_id"),

                call_id=call_id,
        ))
