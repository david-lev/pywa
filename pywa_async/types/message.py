"""This module contains the types related to messages."""

from __future__ import annotations

__all__ = ["Message"]

from types import MappingProxyType

from pywa.types.message import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.message import Message as _Message  # noqa MUST BE IMPORTED FIRST


import dataclasses
from typing import TYPE_CHECKING, Iterable, Callable, Any

from .base_update import BaseUserUpdateAsync  # noqa
from .callback import Button, ButtonUrl, SectionList
from .media import Audio, Document, Image, Sticker, Video
from .others import (
    MessageType,
    ProductsSection,
    Location,
    Order,
    Reaction,
    System,
    Contact,
)

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .sent_message import SentMessage


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Message(BaseUserUpdateAsync, _Message):
    """
    A message received from a user.

    - `'Message' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#messages-object>`_

    Attributes:
        id: The message ID (If you want to reply to the message, use ``message_id_to_reply`` instead).
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (See :class:`MessageType`).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this message is a reply to. (Optional)
        forwarded: Whether the message was forwarded.
        forwarded_many_times: Whether the message was forwarded many times.
         (when True, ``forwarded`` will be True as well)
        text: The text of the message (if the message type is :class:`MessageType.TEXT`).
        image: The image of the message (if the message type is :class:`MessageType.IMAGE`).
        video: The video of the message (if the message type is :class:`MessageType.VIDEO`).
        sticker: The sticker of the message (if the message type is :class:`MessageType.STICKER`).
        document: The document of the message (if the message type is :class:`MessageType.DOCUMENT`).
        audio: The audio of the message (if the message type is :class:`MessageType.AUDIO`).
        caption: The caption of the message (Optional, only available for :class:`MessageType.IMAGE`,
         :class:`MessageType.VIDEO` and :class:`MessageType.DOCUMENT`).
        reaction: The reaction of the message (if the message type is :class:`MessageType.REACTION`).
        location: The location of the message (if the message type is :class:`MessageType.LOCATION`).
        contacts: The contacts of the message (if the message type is :class:`MessageType.CONTACTS`).
        order: The order of the message (if the message type is :class:`MessageType.ORDER`).
        system: The system update (if the message type is :class:`MessageType.SYSTEM`).
        error: The error of the message (if the message type is :class:`MessageType.UNSUPPORTED`).
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)

    image: Image | None = None
    video: Video | None = None
    sticker: Sticker | None = None
    document: Document | None = None
    audio: Audio | None = None
    _fields_to_objects_constructors = MappingProxyType(
        _Message._fields_to_objects_constructors
        | dict(
            image=Image.from_dict,
            video=Video.from_dict,
            sticker=Sticker.from_dict,
            document=Document.from_dict,
            audio=Audio.from_dict,
        )
    )

    @property
    def media(
        self,
    ) -> Image | Video | Sticker | Document | Audio | None:
        """
        The media of the message if any, otherwise ``None``. (image, video, sticker, document or audio)
            - If you want to check whether the message has any media, use :attr:`~Message.has_media` instead.
        """
        return next(
            (
                getattr(self, media_type)
                for media_type in self._media_fields
                if getattr(self, media_type)
            ),
            None,
        )

    async def download_media(
        self,
        filepath: str | None = None,
        filename: str | None = None,
        in_memory: bool = False,
        **kwargs,
    ) -> str | bytes:
        """
        Download a media file from WhatsApp servers (image, video, sticker, document or audio).

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file (if not provided, it will be guessed from the URL + extension).
            in_memory: Whether to return the file as bytes instead of saving it to disk (default: False).
            **kwargs: Additional arguments to pass to httpx.get.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.

        Raises:
            ValueError: If the message does not contain any media.
        """
        try:
            return await self.media.download(
                path=filepath, filename=filename, in_memory=in_memory, **kwargs
            )
        except AttributeError:
            raise ValueError("Message does not contain any media.")

    async def copy(
        self,
        to: str,
        header: str | None = None,
        body: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | SectionList | None = None,
        preview_url: bool = False,
        reply_to_message_id: str = None,
        tracker: str | None = None,
        sender: str | int | None = None,
    ) -> SentMessage:
        """
        Send the message to another user.

            - The WhatsApp Cloud API does not offer a `real` forward option, so this method will send a new message with the same content as the original message.
            - Supported message types: ``TEXT``, ``DOCUMENT``, ``IMAGE``, ``VIDEO``, ``STICKER``, ``LOCATION``, ``AUDIO``, ``CONTACTS``, ``ORDER`` and ``SYSTEM``.
            - If the message type is ``reaction``, you must provide ``reply_to_message_id``.

        Args:
            to: The phone ID of the WhatsApp user to copy the message to.
            header: The header of the message (if keyboard is provided, optional, up to 60 characters, no markdown allowed).
            body: The body of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).
            buttons: The buttons to send with the message (only in case of message from type ``text``, ``document``,
             ``video`` and ``image``. also, the ``SectionList`` is only available to ``text`` type)
            reply_to_message_id:  The message ID to reply to (optional).
            preview_url: Whether to show a preview of the URL in the message (if any).
            tracker: The track data of the message.
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The ID of the sent message.

        Raises:
            ValueError: If the message type is ``reaction`` and no ``reply_to_message_id`` is provided, or if the message
             type is ``unsupported``.
        """
        match self.type:
            case MessageType.TEXT:
                return await self._client.send_message(
                    sender=sender,
                    to=to,
                    text=self.text,
                    preview_url=preview_url,
                    header=header,
                    footer=footer,
                    buttons=buttons,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.DOCUMENT:
                return await self._client.send_document(
                    sender=sender,
                    to=to,
                    document=self.document.id,
                    filename=self.document.filename,
                    caption=self.caption,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.IMAGE:
                return await self._client.send_image(
                    sender=sender,
                    to=to,
                    image=self.image.id,
                    caption=self.caption,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.VIDEO:
                return await self._client.send_video(
                    sender=sender,
                    to=to,
                    video=self.video.id,
                    caption=self.caption,
                    buttons=buttons,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.STICKER:
                return await self._client.send_sticker(
                    sender=sender, to=to, sticker=self.sticker.id, tracker=tracker
                )
            case MessageType.LOCATION:
                return await self._client.send_location(
                    sender=sender,
                    to=to,
                    latitude=self.location.latitude,
                    longitude=self.location.longitude,
                    name=self.location.name,
                    address=self.location.address,
                    tracker=tracker,
                )
            case MessageType.AUDIO:
                return await self._client.send_audio(
                    sender=sender, to=to, audio=self.audio.id, tracker=tracker
                )
            case MessageType.CONTACTS:
                return await self._client.send_contact(
                    sender=sender,
                    to=to,
                    contact=self.contacts,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.REACTION:
                if reply_to_message_id is None:
                    raise ValueError(
                        "You need to provide `reply_to_message_id` in order to `copy` a reaction"
                    )
                return await self._client.send_reaction(
                    sender=sender,
                    to=to,
                    message_id=reply_to_message_id,
                    emoji=self.reaction.emoji or "",
                )
            case MessageType.ORDER:
                if len(self.order.products) == 1:
                    return await self._client.send_product(
                        sender=sender,
                        to=to,
                        catalog_id=self.order.catalog_id,
                        sku=self.order.products[0].sku,
                        body=body,
                        footer=footer,
                        reply_to_message_id=reply_to_message_id,
                    )
                return await self._client.send_products(
                    sender=sender,
                    to=to,
                    catalog_id=self.order.catalog_id,
                    product_sections=(
                        ProductsSection(
                            title=header,
                            skus=(p.sku for p in self.order.products),
                        ),
                    ),
                    title=header,
                    body=body,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                )
            case MessageType.SYSTEM:
                return await self._client.send_message(
                    sender=sender,
                    to=to,
                    text=self.system.body,
                    header=header,
                    footer=footer,
                    buttons=buttons,
                    reply_to_message_id=reply_to_message_id,
                )
            case _:
                raise ValueError(f"Message of type {self.type} cannot be copied.")
