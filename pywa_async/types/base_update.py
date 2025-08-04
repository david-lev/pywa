"""This module contains the base types for all update types."""

from __future__ import annotations

__all__ = [
    "StopHandling",
    "ContinueHandling",
]

from pywa.types.base_update import *  # noqa MUST BE IMPORTED FIRST

import pathlib
import dataclasses
from typing import TYPE_CHECKING, BinaryIO, Iterable

from .others import Contact, ProductsSection, User, SuccessResult


if TYPE_CHECKING:
    from ..client import WhatsApp
    from .calls import SessionDescription
    from pywa.types.sent_update import InitiatedCall
    from .sent_update import SentMessage, SentTemplate
    from .callback import (
        Button,
        URLButton,
        VoiceCallButton,
        SectionList,
        FlowButton,
        CallbackData,
    )
    from .templates import TemplateLanguage, TemplateBaseComponent


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
            | SectionList
            | FlowButton
            | None
        ) = None,
        *,
        quote: bool = False,
        preview_url: bool = False,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with text.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_message` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> msg.reply_text(
            ...     text="Hello from PyWa! (https://github.com/david-lev/pywa)",
            ...     quote=True,
            ... )

        Args:
            text: The text to reply with (markdown allowed, max 4096 characters).
            header: The header of the reply (if buttons are provided, optional, up to 60 characters,
             no markdown allowed).
            footer: The footer of the reply (if buttons are provided, optional, up to 60 characters,
             markdown has no effect).
            buttons: The buttons to send with the message (optional).
            quote: Whether to quote the replied message (default: False).
            preview_url: Whether to show a preview of the URL in the message (if any).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
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
            tracker=tracker,
        )

    reply = reply_text  # alias

    async def reply_image(
        self,
        image: str | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with an image.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_image` with ``to`` and ``reply_to_message_id``.
            - Images must be 8-bit, RGB or RGBA.

        Example:

            >>> msg.reply_image(
            ...     image="https://example.com/image.png",
            ...     caption="This is an image!",
            ...     quote=True,
            ... )

        Args:
            image: The image to reply (either a media ID, URL, file path, bytes, or an open file object. When buttons are
             provided, only URL is supported).
            caption: The caption of the image (required when buttons are provided,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the image (optional).
            mime_type: The mime type of the image (optional, required when sending an image as bytes or a file object,
             or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
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
            tracker=tracker,
        )

    async def reply_video(
        self,
        video: str | pathlib.Path | bytes | BinaryIO,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a video.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_video` with ``to`` and ``reply_to_message_id``.
            - Only H.264 video codec and AAC audio codec is supported.
            - Videos with a single audio stream or no audio stream are supported.

        Example:

            >>> msg.reply_video(
            ...     video="https://example.com/video.mp4",
            ...     caption="This is a video",
            ...     quote=True,
            ... )

        Args:
            video: The video to reply (either a media ID, URL, file path, bytes, or an open file object. When buttons
             are provided, only URL is supported).
            caption: The caption of the video (required when sending a video with buttons,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if ``buttons`` are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the video (optional).
            mime_type: The mime type of the video (optional, required when sending a video as bytes or a file object,
             or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
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
            tracker=tracker,
        )

    async def reply_document(
        self,
        document: str | pathlib.Path | bytes | BinaryIO,
        filename: str | None = None,
        caption: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | URLButton | FlowButton | None = None,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a document.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_document` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> msg.reply_document(
            ...     document="https://example.com/example_123.pdf",
            ...     filename="example.pdf",
            ...     caption="Example PDF",
            ...     quote=True,
            ... )


        Args:
            document: The document to reply (either a media ID, URL, file path, bytes, or an open file object. When
             buttons are provided, only URL is supported).
            filename: The filename of the document (optional, The extension of the filename will specify what format the
             document is displayed as in WhatsApp).
            caption: The caption of the document (required when sending a document with buttons,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ allowed).
            footer: The footer of the message (if buttons are provided, optional,
             `markdown <https://faq.whatsapp.com/539178204879377>`_ has no effect).
            buttons: The buttons to send with the document (optional).
            mime_type: The mime type of the document (optional, required when sending a document as bytes or a file
             object, or file path that does not have an extension).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
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
            tracker=tracker,
        )

    async def reply_audio(
        self,
        audio: str | pathlib.Path | bytes | BinaryIO,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with an audio.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_audio` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> msg.reply_audio(
            ...     audio='https://example.com/audio.mp3',
            ... )

        Args:
            audio: The audio file to reply with (either a media ID, URL, file path, bytes, or an open file object).
            quote: Whether to quote the replied message (default: False).
            mime_type: The mime type of the audio (optional, required when sending a audio as bytes or a file object,
             or file path that does not have an extension).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent message.
        """
        return await self._client.send_audio(
            sender=self._internal_recipient,
            to=self._internal_sender,
            audio=audio,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
            tracker=tracker,
        )

    async def reply_sticker(
        self,
        sticker: str | pathlib.Path | bytes | BinaryIO,
        *,
        quote: bool = False,
        mime_type: str | None = None,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a sticker.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_sticker` with ``to`` and ``reply_to_message_id``.
            - A static sticker needs to be 512x512 pixels and cannot exceed 100 KB.
            - An animated sticker must be 512x512 pixels and cannot exceed 500 KB.

        Example:

            >>> msg.reply_sticker(
            ...     sticker='https://example.com/sticker.webp',
            ... )

        Args:
            sticker: The sticker to reply with (either a media ID, URL, file path, bytes, or an open file object).
            quote: Whether to quote the replied message (default: False).
            mime_type: The mime type of the sticker (optional, required when sending a sticker as bytes or a file
             object, or file path that does not have an extension).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.send_sticker(
            sender=self._internal_recipient,
            to=self._internal_sender,
            sticker=sticker,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            mime_type=mime_type,
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
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a location.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_location` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> msg.reply_location(
            ...     latitude=37.4847483695049,
            ...     longitude=--122.1473373086664,
            ...     name='WhatsApp HQ',
            ...     address='Menlo Park, 1601 Willow Rd, United States',
            ... )


        Args:
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location (optional).
            address: The address of the location (optional).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.send_location(
            sender=self._internal_recipient,
            to=self._internal_sender,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            tracker=tracker,
        )

    async def reply_location_request(
        self,
        text: str,
        *,
        quote: bool = False,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a request for the user's location.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.request_location` with ``to`` and ``reply_to_message_id``.

        Example:

                >>> msg.reply_location_request(
                ...     text='Please share your location',
                ... )


        Args:
            text: The text to send with the request.
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.request_location(
            sender=self._internal_recipient,
            to=self._internal_sender,
            text=text,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            tracker=tracker,
        )

    async def reply_contact(
        self,
        contact: Contact | Iterable[Contact],
        *,
        quote: bool = False,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a contact/s.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_contact` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> from pywa.types import Contact
            >>> msg.reply_contact(
            ...     contact=Contact(
            ...         name=Contact.Name(formatted_name='David Lev', first_name='David'),
            ...         phones=[Contact.Phone(phone='1234567890', wa_id='1234567890', type='MOBILE')],
            ...         emails=[Contact.Email(email='test@test.com', type='WORK')],
            ...         urls=[Contact.Url(url='https://exmaple.com', type='HOME')],
            ...      ),
            ...     quote=True,
            ... )


        Args:
            contact: The contact/s to send.
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.send_contact(
            sender=self._internal_recipient,
            to=self._internal_sender,
            contact=contact,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            tracker=tracker,
        )

    async def react(
        self, emoji: str, *, tracker: str | CallbackData | None = None
    ) -> SentMessage:
        """
        React to the message with an emoji.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_reaction` with ``to`` and ``message_id``.

        Example:

            >>> msg.react('👍')

        Args:
            emoji: The emoji to react with.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reaction.
        """
        return await self._client.send_reaction(
            sender=self._internal_recipient,
            to=self._internal_sender,
            emoji=emoji,
            message_id=self.message_id_to_reply,
            tracker=tracker,
        )

    async def unreact(
        self, *, tracker: str | CallbackData | None = None
    ) -> SentMessage:
        """
        Remove the reaction from the message.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.remove_reaction` with ``to`` and ``message_id``.

        Example:

            >>> msg.unreact()

        Args:
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent unreaction.
        """
        return await self._client.remove_reaction(
            sender=self._internal_recipient,
            to=self._internal_sender,
            message_id=self.message_id_to_reply,
            tracker=tracker,
        )

    async def reply_catalog(
        self,
        body: str,
        footer: str | None = None,
        *,
        thumbnail_product_sku: str | None = None,
        quote: bool = False,
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a catalog.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_catalog` with ``to`` and ``reply_to_message_id``.

        Example:

            >>> msg.reply_catalog(
            ...     body='This is a catalog',
            ...     footer='Powered by PyWa',
            ...     thumbnail_product_sku='SKU123',
            ... )

        Args:
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            thumbnail_product_sku: The thumbnail of this item will be used as the message's header image (optional, if
                not provided, the first item in the catalog will be used).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.send_catalog(
            sender=self._internal_recipient,
            to=self._internal_sender,
            body=body,
            footer=footer,
            thumbnail_product_sku=thumbnail_product_sku,
            reply_to_message_id=self.message_id_to_reply if quote else None,
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
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a product.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_product` with ``to`` and ``reply_to_message_id``.
            - To reply with multiple products, use :py:func:`~BaseUserUpdate.reply_products`.

        Args:
            catalog_id: The ID of the catalog to send the product from. (To get the catalog ID use
             :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager
             <https://business.facebook.com/commerce/>`_).
            sku: The product SKU to send.
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
        """
        return await self._client.send_product(
            sender=self._internal_recipient,
            to=self._internal_sender,
            catalog_id=catalog_id,
            sku=sku,
            body=body,
            footer=footer,
            reply_to_message_id=self.message_id_to_reply if quote else None,
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
        tracker: str | CallbackData | None = None,
    ) -> SentMessage:
        """
        Reply to the message with a product.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.send_products` with ``to`` and ``reply_to_message_id``.
            - To reply with multiple products, use :py:func:`~BaseUserUpdate.reply_products`.

        Example:

            >>> from pywa.types import ProductsSection
            >>> msg.reply_products(
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
            ...     quote=True,
            ... )


        Args:
            catalog_id: The ID of the catalog to send the product from (To get the catalog ID
             use :py:func:`~pywa.client.WhatsApp.get_commerce_settings` or in the `Commerce Manager <https://business.facebook.com/commerce/>`_).
            product_sections: The product sections to send (up to 30 products across all sections).
            title: The title of the product list (up to 60 characters).
            body: Text to appear in the message body (up to 1024 characters).
            footer: Text to appear in the footer of the message (optional, up to 60 characters).
            quote: Whether to quote the replied message (default: False).
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent reply.
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
            tracker=tracker,
        )

    async def reply_template(
        self,
        name: str,
        language: TemplateLanguage,
        params: list[TemplateBaseComponent.Params],
        *,
        quote: bool = False,
        tracker: str | CallbackData | None = None,
    ) -> SentTemplate:
        """
        Reply to the message with a template.

        -- Shortcut for :py:func:`~pywa.client.WhatsApp.send_template` with ``to`` and ``reply_to_message_id``.

        Args:
            name: The name of the template to send.
            language: The language of the template to send.
            params: The parameters to fill in the template.
            quote: Whether to quote the replied message (default: False).
            tracker: A callback data to track the message (optional, can be a string or a :class:`CallbackData` object).
        """

        return await self._client.send_template(
            sender=self._internal_recipient,
            to=self._internal_sender,
            name=name,
            language=language,
            params=params,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            tracker=tracker,
        )

    async def mark_as_read(self) -> SuccessResult:
        """
        Mark the message as read.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.mark_message_as_read` with ``message_id``.

        Returns:
            Whether it was successful.
        """
        return await self._client.mark_message_as_read(
            sender=self._internal_recipient, message_id=self.message_id_to_reply
        )

    async def indicate_typing(self) -> SuccessResult:
        """
        Mark the message as read and display a typing indicator so the WhatsApp user knows you are preparing a response.
        This is good practice if it will take you a few seconds to respond.

        The typing indicator will be dismissed once you respond, or after 25 seconds, whichever comes first. To prevent a poor user experience, only display a typing indicator if you are going to respond.

        - Shortcut for :py:func:`~pywa.client.WhatsApp.indicate_typing` with ``message_id``.

        Returns:
            Whether it was successful.
        """
        return await self._client.indicate_typing(
            sender=self._internal_recipient, message_id=self.message_id_to_reply
        )

    async def call(
        self, sdp: SessionDescription, *, tracker: str | CallbackData | None = None
    ) -> InitiatedCall:
        """
        Initiate a call with the user.
            - Shortcut for :py:func:`~pywa.client.WhatsApp.call` with ``to`` and ``message_id``.

        Args:
            sdp: The SDP object containing the call information.
            tracker: The data to track the message with (optional, up to 512 characters, for complex data You can use :class:`CallbackData`).

        Returns:
            The ID of the sent call.
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
