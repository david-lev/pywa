from __future__ import annotations

from types import MappingProxyType

"""This module contains the types related to messages."""

__all__ = ["Message"]

import dataclasses
import datetime
from typing import TYPE_CHECKING, Iterable

from ..errors import WhatsAppError

from .base_update import BaseUserUpdate  # noqa
from .callback import Button, ButtonUrl, SectionList
from .media import Audio, Document, Image, Sticker, Video
from .others import (
    Contact,
    Location,
    MessageType,
    Metadata,
    Order,
    ProductsSection,
    Reaction,
    ReplyToMessage,
    System,
    User,
)

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Message(BaseUserUpdate):
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

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage | None
    forwarded: bool
    forwarded_many_times: bool
    text: str | None = None
    image: Image | None = None
    video: Video | None = None
    sticker: Sticker | None = None
    document: Document | None = None
    audio: Audio | None = None
    caption: str | None = None
    reaction: Reaction | None = None
    location: Location | None = None
    contacts: tuple[Contact, ...] | None = None
    order: Order | None = None
    system: System | None = None
    error: WhatsAppError | None = None

    _media_fields = {"image", "video", "sticker", "document", "audio"}
    _txt_fields = ("text", "caption")
    _fields_to_objects_constructors = MappingProxyType(
        dict(
            text=lambda m, _client: m["body"],
            image=Image.from_dict,
            video=Video.from_dict,
            sticker=Sticker.from_dict,
            document=Document.from_dict,
            audio=Audio.from_dict,
            reaction=Reaction.from_dict,
            location=Location.from_dict,
            contacts=lambda m, _client: tuple(Contact.from_dict(c) for c in m),
            order=Order.from_dict,
            system=System.from_dict,
        )
    )
    """A mapping of message types to their respective constructors."""

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to."""
        return (
            self.id if self.type != MessageType.REACTION else self.reaction.message_id
        )

    @property
    def has_media(self) -> bool:
        """
        Whether the message has any media. (image, video, sticker, document or audio)
            - If you want to get the media of the message, use :attr:`~Message.media` instead.
        """
        return self.media is not None

    @property
    def is_reply(self) -> bool:
        """
        Whether the message is a reply to another message.

        - Reaction messages are also considered as replies (But ``.reply_to_message`` will be ``None``).
        """
        return self.reply_to_message is not None or self.reaction is not None

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> Message:
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        error = value.get("errors", msg.get("errors", (None,)))[0]
        msg_type = msg["type"]
        context = msg.get("context", {})
        constructor = cls._fields_to_objects_constructors.get(msg_type)
        # noinspection PyArgumentList
        msg_content = (
            {msg_type: constructor(msg[msg_type], _client=client)}
            if constructor is not None
            else {}
        )
        try:
            usr = User.from_dict(value["contacts"][0])
        except KeyError:
            usr = User(
                wa_id=msg["from"], name=None
            )  # some messages don't have contacts
        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            type=MessageType(msg_type),
            **msg_content,
            from_user=usr,
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            metadata=Metadata.from_dict(value["metadata"]),
            forwarded=context.get("forwarded", False)
            or context.get("frequently_forwarded", False),
            forwarded_many_times=context.get("frequently_forwarded", False),
            reply_to_message=ReplyToMessage.from_dict(context),
            caption=msg.get(msg_type, {}).get("caption")
            if msg_type in cls._media_fields
            else None,
            error=WhatsAppError.from_dict(error=error) if error is not None else None,
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

    def download_media(
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
            **kwargs: Additional arguments to pass to requests.get.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.

        Raises:
            ValueError: If the message does not contain any media.
        """
        try:
            return self.media.download(
                path=filepath, filename=filename, in_memory=in_memory, **kwargs
            )
        except AttributeError:
            raise ValueError("Message does not contain any media.")

    def copy(
        self,
        to: str,
        header: str | None = None,
        body: str | None = None,
        footer: str | None = None,
        buttons: Iterable[Button] | ButtonUrl | SectionList | None = None,
        preview_url: bool = False,
        reply_to_message_id: str = None,
        keyboard: None = None,
        tracker: str | None = None,
        sender: str | int | None = None,
    ) -> str:
        """
        Send the message to another user.

            - The WhatsApp Cloud API does not offer a `real` forward option, so this method will send a new message with the same content as the original message.
            - Supported message types: ``TEXT``, ``DOCUMENT``, ``IMAGE``, ``VIDEO``, ``STICKER``, ``LOCATION``, ``AUDIO``, ``CONTACTS``, ``ORDER`` and ``SYSTEM``.
            - If the message type is ``reaction``, you must provide ``reply_to_message_id``.

        Args:
            to: The phone ID of the WhatsApp user to copy the message to.
            header: The header of the message (if keyboard is provided, optional, up to 60 characters, no markdown allowed).
            body: The body of the message (if keyboard are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if keyboard is provided, optional, markdown has no effect).
            buttons: The buttons to send with the message (only in case of message from type ``text``, ``document``,
             ``video`` and ``image``. also, the ``SectionList`` is only available to ``text`` type)
            reply_to_message_id:  The message ID to reply to (optional).
            preview_url: Whether to show a preview of the URL in the message (if any).
            keyboard: Deprecated and will be removed in a future version, use ``buttons`` instead.
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
                return self._client.send_message(
                    sender=sender,
                    to=to,
                    text=self.text,
                    preview_url=preview_url,
                    header=header,
                    footer=footer,
                    buttons=buttons,
                    reply_to_message_id=reply_to_message_id,
                    keyboard=keyboard,
                    tracker=tracker,
                )
            case MessageType.DOCUMENT:
                return self._client.send_document(
                    sender=sender,
                    to=to,
                    document=self.document.id,
                    filename=self.document.filename,
                    caption=self.caption,
                    body=body,
                    footer=footer,
                    buttons=keyboard or buttons,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.IMAGE:
                return self._client.send_image(
                    sender=sender,
                    to=to,
                    image=self.image.id,
                    caption=self.caption,
                    body=body,
                    footer=footer,
                    buttons=keyboard or buttons,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.VIDEO:
                return self._client.send_video(
                    sender=sender,
                    to=to,
                    video=self.video.id,
                    caption=self.caption,
                    buttons=keyboard or buttons,
                    body=body,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.STICKER:
                return self._client.send_sticker(
                    sender=sender, to=to, sticker=self.sticker.id, tracker=tracker
                )
            case MessageType.LOCATION:
                return self._client.send_location(
                    sender=sender,
                    to=to,
                    latitude=self.location.latitude,
                    longitude=self.location.longitude,
                    name=self.location.name,
                    address=self.location.address,
                    tracker=tracker,
                )
            case MessageType.AUDIO:
                return self._client.send_audio(
                    sender=sender, to=to, audio=self.audio.id, tracker=tracker
                )
            case MessageType.CONTACTS:
                return self._client.send_contact(
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
                return self._client.send_reaction(
                    sender=sender,
                    to=to,
                    message_id=reply_to_message_id,
                    emoji=self.reaction.emoji or "",
                )
            case MessageType.ORDER:
                if len(self.order.products) == 1:
                    return self._client.send_product(
                        sender=sender,
                        to=to,
                        catalog_id=self.order.catalog_id,
                        sku=self.order.products[0].sku,
                        body=body,
                        footer=footer,
                        reply_to_message_id=reply_to_message_id,
                    )
                return self._client.send_products(
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
                return self._client.send_message(
                    sender=sender,
                    to=to,
                    text=self.system.body,
                    header=header,
                    footer=footer,
                    buttons=keyboard,
                    reply_to_message_id=reply_to_message_id,
                )
            case _:
                raise ValueError(f"Message of type {self.type} cannot be copied.")
