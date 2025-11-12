"""This module contains the base types for all update types."""

from __future__ import annotations

from pywa.types.base_update import *  # noqa MUST BE IMPORTED FIRST

import pathlib
import dataclasses
from typing import TYPE_CHECKING, BinaryIO, Iterable, Iterator, AsyncIterator

from pywa.types.templates import BaseParams
from .others import Contact, ProductsSection, User, SuccessResult


if TYPE_CHECKING:
    from ..client import WhatsApp
    from .calls import SessionDescription
    from pywa.types.sent_update import InitiatedCall
    from .sent_update import (
        SentMessage,
        SentTemplate,
        SentVoiceMessage,
        SentLocationRequest,
        SentMediaMessage,
    )
    from .callback import (
        Button,
        URLButton,
        VoiceCallButton,
        SectionList,
        FlowButton,
        CallbackData,
        CallPermissionRequestButton,
    )
    from .templates import TemplateLanguage
    from .media import Media


class _ClientShortcutsAsync:
    """Async Base class for all user-related update types (message, callback, etc.)."""

    message_id_to_reply: str
    """
    The ID of the message to reply to.

    If you want to ``wa.send_x`` with ``reply_to_message_id`` in order to reply to a message, use this property
    instead of ``id`` to prevent errors.
    """
    from_user: User
    """The user who sent the message."""
    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _internal_sender: str
    _internal_recipient: str

    async def reply_text(
        self,
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
        quote: bool = False,
        preview_url: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with text.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_message` with ``to`` and ``reply_to_message_id``.
        - Text messages are messages containing text and an optional link preview.
        - You can have the WhatsApp client attempt to render a preview of the first URL in the body text string, if it contains one. URLs must begin with ``http://`` or ``https://``. If multiple URLs are in the body text string, only the first URL will be rendered. If omitted, or if unable to retrieve a link preview, a clickable link will be rendered instead.
        - See `Text messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages>`_.
        - See `Markdown <https://faq.whatsapp.com/539178204879377>`_ for formatting text messages.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply(f"Hello {msg.from_user.name}! This is a reply to your message.", quote=True)

        Args:
            text: The text to reply with (`markdown <https://faq.whatsapp.com/539178204879377>`_ allowed, max 4096 characters).
            header: The header of the message (if ``buttons`` are provided, optional, up to 60 characters, no `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if ``buttons`` are provided, optional, up to 60 characters, `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the message (optional).
            quote: Whether to quote the replied message (default: False).
            preview_url: Whether to show a preview of the URL in the message (if any).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent text message.
        """
        return await self._client.send_message(
            sender=self._internal_recipient,
            to=self._internal_sender,
            text=text,
            header=header,
            footer=footer,
            buttons=buttons,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            preview_url=preview_url,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    reply = reply_text  # alias

    async def reply_image(
        self,
        image: (
            str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes]
        ),
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMediaMessage:
        """
        Reply to the message with an image.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_image` with ``to`` and ``reply_to_message_id``.
        - Image messages are messages that display a single image and an optional caption.
        - See `Image messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages>`_.
        - See `Supported image formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages#supported-image-formats>`_.
        - Images must be 8-bit, RGB or RGBA.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_image(
            ...         image="https://example.com/image.jpg",
            ...         caption="This is an image",
            ...     )

        Args:
            image: The image to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            caption: The caption of the image (required when buttons are provided, `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional, `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the image (optional).
            quote: Whether to quote the replied message (default: False).
            mime_type: The mime type of the image (optional, required when sending an image as bytes, or file path that does not have an extension).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent image message.
        """
        return await self._client.send_image(
            sender=self._internal_recipient,
            to=self._internal_sender,
            image=image,
            caption=caption,
            footer=footer,
            buttons=buttons,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_video(
        self,
        video: (
            str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes]
        ),
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMediaMessage:
        """
        Reply to the message with a video.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_video` with ``to`` and ``reply_to_message_id``.
        - Video messages display a thumbnail preview of a video image with an optional caption. When the WhatsApp user taps the preview, it loads the video and displays it to the user.
        - Only H.264 video codec and AAC audio codec supported. Single audio stream or no audio stream only.
        - See `Video messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages>`_.
        - See `Supported video formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages#supported-video-formats>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_video(
            ...         video="https://example.com/video.mp4",
            ...         caption="This is a video",
            ...     )

        Args:
            video: The video to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            caption: The caption of the video (required when sending a video with buttons, `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional, `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the video (optional).
            quote: Whether to quote the replied message (default: False).
            mime_type: The mime type of the video (optional, required when sending a video as bytes or file path that does not have an extension).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent video message.
        """
        return await self._client.send_video(
            sender=self._internal_recipient,
            to=self._internal_sender,
            video=video,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            buttons=buttons,
            footer=footer,
            mime_type=mime_type,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_document(
        self,
        document: (
            str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes]
        ),
        filename: str | None = None,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMediaMessage:
        """
        Reply to the message with a document.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_document` with ``to`` and ``reply_to_message_id``.
        - Document messages are messages that display a document icon, linked to a document, that a WhatsApp user can tap to download.
        - See `Document messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages>`_.
        - See `Supported document types <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages#supported-document-types>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_document(
            ...         document="https://example.com/document.pdf",
            ...         filename="document.pdf",
            ...         caption="This is a document",
            ...     )

        Args:
            document: The document to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            filename: Document filename, with extension. The WhatsApp client will use an appropriate file type icon based on the extension (Optional, if not provided, if possible, the filename will be extracted from the media. pass ``None`` to skip this behavior).
            caption: The caption of the document (required when sending a document with buttons, `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional, `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the document (optional).
            quote: Whether to quote the replied message (default: False).
            mime_type: The mime type of the document (optional, required when sending a document as bytes or file path that does not have an extension).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent document message.
        """
        return await self._client.send_document(
            sender=self._internal_recipient,
            to=self._internal_sender,
            document=document,
            filename=filename,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            buttons=buttons,
            footer=footer,
            mime_type=mime_type,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_audio(
        self,
        audio: (
            str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes]
        ),
        *,
        is_voice: bool | None = None,
        quote: bool = False,
        mime_type: str | None = None,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMediaMessage:
        """
        Reply to the message with an audio.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_audio` with ``to`` and ``reply_to_message_id``.
        - Basic audio messages display a download icon and a music icon. When the WhatsApp user taps the play icon, the user must manually download the audio message for the WhatsApp client to load and then play the audio file.
        - See `Audio messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/audio-messages#basic-audio-messages>`_.
        - See `Supported audio formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/audio-messages#supported-audio-formats>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_audio(audio="https://example.com/audio.mp3")

        Args:
            audio: The audio file to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            is_voice: Set to True if sending a voice message (use :meth:`~pywa.types.base_update.BaseUserUpdate.reply_voice` instead for better type support).
            mime_type: The mime type of the audio file (optional, required when sending an audio as bytes or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent audio message.
        """
        return await self._client.send_audio(
            sender=self._internal_recipient,
            to=self._internal_sender,
            audio=audio,
            is_voice=is_voice,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_voice(
        self,
        voice: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentVoiceMessage:
        """
        Reply to the message with a voice message.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_voice` with ``to`` and ``reply_to_message_id``.
        - A voice message (sometimes referred to as a voice note, voice memo, or audio) is a recording of one or more persons speaking, and can include background sounds like music. Voice messages include features like automatic download, profile picture, and voice icon, not available with a basic audio message. If the user has set voice message transcripts to Automatic, a text transcription of the message will also be included.
        - See `Voice messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/audio-messages#voice-messages>`_.
        - Voice messages require .ogg files encoded with the OPUS codec. If you send a different file type or a file encoded with a different codec, voice message transcription will fail.
        - The play icon will only appear if the file is 512KB or smaller, otherwise it will be replaced with a download icon (a downward facing arrow).
        - Your business's profile image is used as the profile image, accompanied by a microphone icon.
        - The text transcription appears if the user has enabled Automatic voice message transcripts. If the user has set this to Manual, the text "Transcribe" will appear instead, which will display the transcribed text once tapped. If the user has set voice message transcripts to Never, no text will appear.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... def callback(_: WhatsApp, msg: Message):
            ...     msg.reply_voice(voice="https://example.com/voice.ogg")

        Args:
            voice: The voice file to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the voice file (optional, required when sending an audio as bytes or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent voice message.
        """
        return await self._client.send_voice(
            sender=self._internal_recipient,
            to=self._internal_sender,
            voice=voice,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
            tracker=tracker,
        )

    async def reply_sticker(
        self,
        sticker: (
            str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes]
        ),
        *,
        quote: bool = False,
        mime_type: str | None = None,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMediaMessage:
        """
        Reply to the message with a sticker.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_sticker` with ``to`` and ``reply_to_message_id``.
        - Sticker messages display animated or static sticker images in a WhatsApp message.
        - A static sticker needs to be 512x512 pixels and cannot exceed 100 KB.
        - An animated sticker must be 512x512 pixels and cannot exceed 500 KB.
        - See `Sticker messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/sticker-messages>`_.
        - See `Supported sticker formats <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/sticker-messages#supported-sticker-formats>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_sticker(sticker="https://example.com/sticker.webp")

        Args:
            sticker: The sticker to reply with (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the sticker (optional, required when sending a sticker as bytes or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent sticker message.
        """
        return await self._client.send_sticker(
            sender=self._internal_recipient,
            to=self._internal_sender,
            sticker=sticker,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_location(
        self,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
        *,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a location.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_location` with ``to`` and ``reply_to_message_id``.
        - Location messages allow you to send a location's latitude and longitude coordinates to a WhatsApp user.
        - Read more about `Location messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/location-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_location(
            ...         latitude=37.4847483695049,
            ...         longitude=-122.1473373086664,
            ...         name='WhatsApp HQ',
            ...        address='Menlo Park, 1601 Willow Rd, United States',
            ...     )

        Args:
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location (optional).
            address: The address of the location (optional).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent location message.
        """
        return await self._client.send_location(
            sender=self._internal_recipient,
            to=self._internal_sender,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_location_request(
        self,
        text: str,
        *,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentLocationRequest:
        """
        Reply to the message with a request for the user's location.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.request_location` with ``to`` and ``reply_to_message_id``.
        - Location request messages display body text and a send location button. When a WhatsApp user taps the button, a location sharing screen appears which the user can then use to share their location.
        - Once the user shares their location, a :class:`Message` update is triggered, containing the user's location details.
        - Read more about `Location request messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/location-request-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_location_request(text='Please share your location')

        Args:
            text: The text to send with the request.
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent location request message.
        """
        return await self._client.request_location(
            sender=self._internal_recipient,
            to=self._internal_sender,
            text=text,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_contact(
        self,
        contact: Contact | Iterable[Contact],
        *,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a contact/s.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_contact` with ``to`` and ``reply_to_message_id``.
        - Contacts messages allow you to send rich contact information directly to WhatsApp users, such as names, phone numbers, physical addresses, and email addresses. When a WhatsApp user taps the message's profile arrow, it displays the contact's information in a profile view:
        - Each message can include information for up to 257 contacts, although it is recommended to send fewer for usability and negative feedback reasons.
        - See `Contacts messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/contacts-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_contact(
            ...         contact=Contact(
            ...             name=Contact.Name(formatted_name='David Lev', first_name='David'),
            ...             phones=[Contact.Phone(phone='1234567890', wa_id='1234567890', type='MOBILE')],
            ...             emails=[Contact.Email(email='test@test.com', type='WORK')],
            ...             urls=[Contact.Url(url='https://exmaple.com', type='HOME')],
            ...         ),
            ...         quote=True,
            ...     )

        Args:
            contact: The contact/s to send.
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent contact/s message.
        """
        return await self._client.send_contact(
            sender=self._internal_recipient,
            to=self._internal_sender,
            contact=contact,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def react(
        self,
        emoji: str,
        *,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        React to the message with an emoji.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_reaction` with ``to`` and ``message_id``.
        - Reaction messages are emoji-reactions that you can apply to a previous WhatsApp user message that you have received.
        - When sending a reaction message, only a :class:`MessageStatus` update (``type`` set to ``SENT``) will be triggered; ``DELIVERED`` and ``READ`` updates will not be triggered.
        - You can react to incoming messages by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.react` method on every update.
        - See `Reaction messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/reaction-messages>`_.

        Example:

        >>> wa = WhatsApp(...)
        >>> @wa.on_message
        ... async def callback(_: WhatsApp, msg: Message):
        ...     await msg.react("👍")

        Args:
            emoji: The emoji to react with.
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent reaction message (You can't use this message id to remove the reaction or perform any other
            action on it. instead, use the message ID of the message you reacted to).
        """
        return await self._client.send_reaction(
            sender=self._internal_recipient,
            to=self._internal_sender,
            emoji=emoji,
            message_id=self.message_id_to_reply,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def unreact(
        self,
        *,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Remove the reaction from the message.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.remove_reaction` with ``to`` and ``message_id``.
        - You can remove reactions from incoming messages by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.unreact` method on every update.
        - See `Reaction messages <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/reaction-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.react("👍")
            ...     await msg.unreact()

        Args:
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent (un)reaction message (You can't use this message id to remove the reaction or perform any other
            action on it. instead, use the message ID of the message you reacted to).
        """
        return await self._client.remove_reaction(
            sender=self._internal_recipient,
            to=self._internal_sender,
            message_id=self.message_id_to_reply,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_catalog(
        self,
        body: str,
        footer: str | None = None,
        *,
        thumbnail_product_sku: str | None = None,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a catalog.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_catalog` with ``to`` and ``reply_to_message_id``.
        - Catalog messages are messages that allow you to showcase your product catalog entirely within WhatsApp.
        - Catalog messages display a product thumbnail header image of your choice, custom body text, a fixed text header, a fixed text sub-header, and a View catalog button.
        - When a customer taps the View catalog button, your product catalog appears within WhatsApp.
        - You must have `inventory uploaded to Meta <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/upload-inventory>`_ in an ecommerce catalog `connected to your WhatsApp Business Account <https://www.facebook.com/business/help/158662536425974>`_.
        - Read more about `Catalog messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#catalog-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.reply_catalog(
            ...         body='Check out our products!',
            ...         footer='Powered by PyWa',
            ...         thumbnail_product_sku='SKU123',  # Optional, if not provided,
            ...         # the first item in the catalog will be used.
            ...     )

        Args:
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            thumbnail_product_sku: The thumbnail of this item will be used as the message's header image (optional, if
                not provided, the first item in the catalog will be used).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent catalog message.
        """
        return await self._client.send_catalog(
            sender=self._internal_recipient,
            to=self._internal_sender,
            body=body,
            footer=footer,
            thumbnail_product_sku=thumbnail_product_sku,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_product(
        self,
        catalog_id: str,
        sku: str,
        body: str | None = None,
        footer: str | None = None,
        *,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a product.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_product` with ``to`` and ``reply_to_message_id``.
        - To reply with multiple products, use :py:func:`~BaseUserUpdate.reply_products`.
        - See `Product messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#product-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... def callback(_: WhatsApp, msg: Message):
            ...     msg.reply_product(
            ...         catalog_id='1234567890',
            ...         sku='SKU123',
            ...         body='Check out this product!',
            ...         footer='Powered by PyWa',
            ...     )

        Args:
            catalog_id: The ID of the catalog to send the product from. (To get the catalog ID use
             :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager
             <https://business.facebook.com/commerce/>`_).
            sku: The product SKU to send.
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent product message.
        """
        return await self._client.send_product(
            sender=self._internal_recipient,
            to=self._internal_sender,
            catalog_id=catalog_id,
            sku=sku,
            body=body,
            footer=footer,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_products(
        self,
        catalog_id: str,
        product_sections: Iterable[ProductsSection],
        title: str,
        body: str,
        footer: str | None = None,
        *,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a product.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_products` with ``to`` and ``reply_to_message_id``.
        - To reply with multiple products, use :py:func:`~BaseUserUpdate.reply_products`.
        - See `Product messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products#product-messages>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...    await msg.reply_products(
            ...        catalog_id='1234567890',
            ...        title='Tech Products',
            ...        body='Check out our products!',
            ...        product_sections=[
            ...            ProductsSection(
            ...                title='Smartphones',
            ...                skus=['IPHONE12', 'GALAXYS21'],
            ...            ),
            ...            ProductsSection(
            ...                title='Laptops',
            ...                skus=['MACBOOKPRO', 'SURFACEPRO'],
            ...            ),
            ...        ],
            ...        footer='Powered by PyWa',
            ...        quote=True,
            ...    )

        Args:
            catalog_id: The ID of the catalog to send the product from (To get the catalog ID
             use :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager <https://business.facebook.com/commerce/>`_).
            product_sections: The product sections to send (up to 30 products across all sections).
            title: The title of the product list (up to 60 characters).
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent products message.
        """
        return await self._client.send_products(
            sender=self._internal_recipient,
            to=self._internal_sender,
            catalog_id=catalog_id,
            product_sections=product_sections,
            title=title,
            body=body,
            footer=footer,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def reply_template(
        self,
        name: str,
        language: TemplateLanguage,
        params: list[BaseParams],
        *,
        use_mm_lite_api: bool = False,
        message_activity_sharing: bool | None = None,
        quote: bool = False,
        identity_key_hash: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentTemplate:
        """
        Reply to the message with a template.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.send_template` with ``to`` and ``reply_to_message_id``.
        - To create a template, use :py:func:`~pywa.client.WhatsApp.create_template`.
        - Read more about `Template Messages <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates>`_.

        Args:
            name: The name of the template to send.
            language: The language of the template to send.
            params: The parameters to fill in the template.
            use_mm_lite_api: Whether to use `Marketing Messages Lite API <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api>`_ (optional, default: False).
            message_activity_sharing: Whether to share message activities (e.g. message read) for that specific marketing message to Meta to help optimize marketing messages (optional, only if ``use_mm_lite_api`` is True).
            quote: Whether to quote the replied message (default: False).
            identity_key_hash: The message would only be delivered if the hash value matches the customer's current hash (Optional, See `Identity Change Check <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/phone-numbers#identity-change-check>`_).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The sent template message.
        """

        return await self._client.send_template(
            sender=self._internal_recipient,
            to=self._internal_sender,
            name=name,
            language=language,
            params=params,
            use_mm_lite_api=use_mm_lite_api,
            message_activity_sharing=message_activity_sharing,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            identity_key_hash=identity_key_hash,
            tracker=tracker,
        )

    async def mark_as_read(self) -> SuccessResult:
        """
        Mark the message as read.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.mark_message_as_read` with ``message_id``.
        - You can mark incoming messages as read by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.mark_as_read` method or indicate typing by using the :py:func:`~pywa.types.base_update.BaseUserUpdate.indicate_typing` method on every update.
        - It's good practice to mark an incoming messages as read within 30 days of receipt. Marking a message as read will also mark earlier messages in the thread as read.
        - Read more about `Mark messages as read <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/mark-message-as-read>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.mark_as_read()

        Returns:
            Whether it was successful.
        """
        return await self._client.mark_message_as_read(
            sender=self._internal_recipient, message_id=self.message_id_to_reply
        )

    async def indicate_typing(self) -> SuccessResult:
        """
        Mark the message as read and display a typing indicator so the WhatsApp user knows you are preparing a response.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.indicate_typing` with ``message_id``.
        - The typing indicator will be dismissed once you respond, or after 25 seconds, whichever comes first. To prevent a poor user experience, only display a typing indicator if you are going to respond.
        - Read more about `Typing indicators <https://developers.facebook.com/docs/whatsapp/cloud-api/typing-indicators>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...     await msg.indicate_typing()

        Returns:
            Whether it was successful.
        """
        return await self._client.indicate_typing(
            sender=self._internal_recipient, message_id=self.message_id_to_reply
        )

    async def call(
        self,
        sdp: SessionDescription,
        *,
        tracker: str | CallbackData | None = None,
    ) -> InitiatedCall:
        """
        Initiate a call with the user.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.call` with ``to`` and ``message_id``.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#initiate-call>`_.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_message
            ... async def callback(_: WhatsApp, msg: Message):
            ...    await msg.call(...)

        Args:
            sdp: The SDP object containing the call information.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data you can use :class:`~pywa.types.callback.CallbackData`).

        Returns:
            The initiated call.
        """
        return await self._client.initiate_call(
            to=self._internal_sender,
            sdp=sdp,
            tracker=tracker,
            phone_id=self._internal_recipient,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class BaseUserUpdateAsync(_ClientShortcutsAsync):
    """Async Base class for all user-related update types (message, callback, etc.)."""

    async def block_sender(self) -> bool:
        """
        Block the sender of the update.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.block_users` with ``sender``.
        """
        return await self.from_user.block()

    async def unblock_sender(self) -> bool:
        """
        Unblock the sender of the update.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.unblock_users` with ``sender``.
        """
        return await self.from_user.unblock()
