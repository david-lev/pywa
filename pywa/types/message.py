from __future__ import annotations

import pathlib

"""This module contains the types related to messages."""

__all__ = [
    "Message",
    "EditedMessage",
    "DeletedMessage",
    "OutgoingMessage",
    "OutgoingEditedMessage",
    "OutgoingDeletedMessage",
]

import dataclasses
import datetime
from typing import TYPE_CHECKING, ClassVar, Generator, Iterable, Type

from ..errors import WhatsAppError
from .base_update import BaseUserUpdate, RawUpdate  # noqa
from .callback import Button, FlowButton, SectionList, URLButton, VoiceCallButton
from .chat import Chat, ChatType
from .media import Audio, Document, Image, Sticker, Video
from .others import (
    ContactList,
    Location,
    MessageType,
    Metadata,
    Order,
    ProductsSection,
    Reaction,
    Referral,
    ReplyToMessage,
    Unsupported,
)
from .user import User

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .sent_update import SentMessage


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
        chat: The chat where the message was sent (private or group).
        timestamp: The timestamp when the message was arrived to WhatsApp servers (in UTC).
        reply_to_message: The message to which this message is a reply (if any).
        forwarded: Whether the message was forwarded.
        forwarded_many_times: Whether the message was forwarded more than 5 times. (when ``True``, ``forwarded`` will be ``True`` as well)
        text: The text of the message.
        image: The image of the message.
        video: The video of the message.
        sticker: The sticker of the message.
        document: The document of the message.
        audio: The audio of the message.
        voice: The voice note of the message (shorthand for ``audio`` if it's a voice note).
        caption: The caption of the message media (Optional, only available for image video and document messages).
        reaction: The reaction of the message.
        location: The location of the message.
        contacts: The contacts of the message.
        order: The order of the message.
        referral: The referral information of the message (When a customer clicks an ad that redirects to WhatsApp).
        unsupported: The unsupported content of the message.
        error: The error of the message.
        shared_data: Shared data between handlers.
    """

    type: MessageType
    reply_to_message: ReplyToMessage | None
    chat: Chat
    forwarded: bool
    forwarded_many_times: bool
    text: str | None = None
    image: Image | None = None
    video: Video | None = None
    sticker: Sticker | None = None
    document: Document | None = None
    audio: Audio | None = None
    reaction: Reaction | None = None
    location: Location | None = None
    contacts: ContactList | None = None
    order: Order | None = None
    referral: Referral | None = None
    unsupported: Unsupported | None = None
    error: WhatsAppError | None = None

    _media_objs: ClassVar[dict] = {
        "image": Image,
        "video": Video,
        "sticker": Sticker,
        "document": Document,
        "audio": Audio,
    }
    _txt_fields = ("text", "caption")
    _webhook_field = "messages"
    _messages_field: ClassVar[str] = "messages"

    @property
    def voice(self) -> Audio | None:
        """Shorthand for the ``audio`` attribute, only if it's a voice note."""
        if self.audio and self.audio.voice:
            return self.audio
        return None

    @property
    def caption(self) -> str | None:
        """The caption of the message media (if any). Only available for image, video and document messages."""
        try:
            return self.media.caption
        except AttributeError:
            return None

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

    def _get_reply_to(self, private: bool = False) -> str:
        if private and self.chat.type == ChatType.GROUP:
            return self.chat.id
        return self._internal_sender

    @classmethod
    def _resolve_msg_content(
        cls,
        *,
        client: WhatsApp,
        msg_type: MessageType,
        content: dict,
        timestamp: datetime.datetime,
        recipient: str,
    ) -> dict:
        match msg_type:
            case MessageType.TEXT:
                return {msg_type.value: content[msg_type.value]["body"]}
            case (
                MessageType.IMAGE
                | MessageType.VIDEO
                | MessageType.STICKER
                | MessageType.DOCUMENT
                | MessageType.AUDIO
            ):
                return {
                    msg_type.value: cls._media_objs[msg_type.value].from_dict(
                        client=client,
                        data=content[msg_type.value],
                        arrived_at=timestamp,
                        received_to=recipient,
                    )
                }
            case MessageType.REACTION:
                return {msg_type.value: Reaction.from_dict(content[msg_type.value])}
            case MessageType.LOCATION:
                return {msg_type.value: Location.from_dict(content[msg_type.value])}
            case MessageType.CONTACTS:
                return {msg_type.value: ContactList(contacts=content)}
            case MessageType.ORDER:
                return {msg_type.value: Order.from_dict(content[msg_type.value])}
            case MessageType.UNSUPPORTED:
                return (
                    {msg_type.value: Unsupported(type=content["unsupported"]["type"])}
                    if "unsupported" in content
                    else {}
                )
            case _:
                return {}

    @classmethod
    def from_update(
        cls, client: WhatsApp, update: RawUpdate, *, is_edit: bool = False
    ) -> Message:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            cls._messages_field
        ][0]
        content = msg["edit"]["message"] if is_edit else msg
        error = value.get("errors", msg.get("errors", (None,)))[0]
        msg_type = content["type"]
        context = content.get("context", {})
        metadata = Metadata.from_dict(value["metadata"])
        timestamp = datetime.datetime.fromtimestamp(
            int(msg["timestamp"]),
            datetime.timezone.utc,
        )
        msg_type = MessageType(msg_type)
        user = client._usr_cls.from_contact(value["contacts"][0], client=client)
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["edit"]["original_message_id"] if is_edit else content["id"],
            type=msg_type,
            **cls._resolve_msg_content(
                client=client,
                msg_type=msg_type,
                content=content,
                timestamp=timestamp,
                recipient=metadata.phone_number_id,
            ),
            from_user=user,
            chat=Chat.from_message(msg=msg, user=user),
            timestamp=timestamp,
            metadata=metadata,
            forwarded=context.get("forwarded", False)
            or context.get("frequently_forwarded", False),
            forwarded_many_times=context.get("frequently_forwarded", False),
            reply_to_message=ReplyToMessage.from_dict(context)
            if context.get("id")
            else None,
            referral=Referral.from_dict(msg["referral"]) if "referral" in msg else None,
            error=WhatsAppError.from_dict(error=error) if error is not None else None,
        )

    @property
    def media(
        self,
    ) -> Image | Video | Sticker | Document | Audio | None:
        """
        The media of the message, if any, otherwise ``None``. (image, video, sticker, document or audio)

        - If you want to check whether the message has any media, use :attr:`~Message.has_media` instead.
        """
        return next(
            (
                getattr(self, media_type)
                for media_type in self._media_objs
                if getattr(self, media_type)
            ),
            None,
        )

    def download_media(
        self,
        filepath: str | None = None,
        filename: str | None = None,
        *,
        chunk_size: int | None = None,
        **httpx_kwargs,
    ) -> pathlib.Path:
        """
        Download the media of the message to the specified path.

        - Shortcut for ``message.media.download(...)``, ``message.image.download(...)`` etc.
        - Use :py:meth:`~pywa.types.message.Message.get_media_bytes` if you want to get the file as bytes instead of saving it to disk.

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.image)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     msg.download_media(path=pathlib.Path('/path/to/save'), filename='my_image.jpg')

        Args:
            filepath: The path where to save the file (if not provided, the current working directory will be used).
            filename: The name of the file to save (if not provided, it will be extracted from the ``Content-Disposition`` header or a SHA256 hash of the URL will be used).
            chunk_size: The size (in bytes) of each chunk to read when downloading the media (default: ``64KB``).
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The path of the saved file if ``in_memory`` is False, the file as bytes otherwise.

        Raises:
            ValueError: If the message does not contain any media.
        """
        try:
            return self.media.download(
                path=filepath,
                filename=filename,
                chunk_size=chunk_size,
                **httpx_kwargs,
            )
        except AttributeError:
            raise ValueError("Message does not contain any media.") from None

    def stream_media(
        self, chunk_size: int | None = None, **httpx_kwargs
    ) -> Generator[bytes]:
        """
        Stream the media of the message as bytes.

        - Shortcut for ``message.media.stream(...)``, ``message.image.stream(...)`` etc.
        - Use :py:meth:`~pywa.types.message.Message.get_media_bytes` if you want to get the whole file as bytes.

        >>> from pywa import WhatsApp, types, filters
        >>> import httpx

        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     with httpx.Client() as client:
        ...        client.post('https://example.com/upload', content=msg.stream_media())

        Args:
            chunk_size: The size (in bytes) of each chunk to read (default: ``64KB``).
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            An iterator that yields chunks of the media file as bytes.

        Raises:
            ValueError: If the message does not contain any media.
        """
        try:
            return self.media.stream(
                chunk_size=chunk_size,
                **httpx_kwargs,
            )
        except AttributeError:
            raise ValueError("Message does not contain any media.") from None

    def get_media_bytes(self, **httpx_kwargs) -> bytes:
        """
        Get the media of the message as bytes.

        - Shortcut for ``message.media.get_bytes(...)``, ``message.image.get_bytes(...)`` etc.
        - Use :py:meth:`~pywa.types.message.Message.stream_media` if you want to stream the file as bytes instead of getting it all at once.

        >>> from pywa import WhatsApp, types, filters
        >>> wa = WhatsApp(...)

        >>> @wa.on_message(filters.document)
        ... def on_message(_: WhatsApp, msg: types.Message):
        ...     doc_bytes = msg.get_media_bytes()

        Args:
            **httpx_kwargs: Additional arguments to pass to ``httpx.get(...)``.

        Returns:
            The media file as bytes.

        Raises:
            ValueError: If the message does not contain any media.
        """
        try:
            return self.media.get_bytes(**httpx_kwargs)
        except AttributeError:
            raise ValueError("Message does not contain any media.") from None

    def copy(
        self,
        to: str,
        header: str | None = None,
        body: str | None = None,
        footer: str | None = None,
        buttons: (
            Iterable[Button]
            | URLButton
            | VoiceCallButton
            | FlowButton
            | SectionList
            | None
        ) = None,
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
            body: The body/caption of the message (if buttons are provided, optional, up to 1024 characters, markdown allowed).
            footer: The footer of the message (if buttons is provided, optional, markdown has no effect).
            buttons: The buttons to send with the message (only in case of message from type ``text``, ``document``,
             ``video`` and ``image``. also, the ``SectionList`` is only available to ``text`` type)
            reply_to_message_id:  The message ID to reply to (optional).
            preview_url: Whether to show a preview of the URL in the message (if any).
            tracker: The track data of the message.
            sender: The phone ID to send the message from (optional, overrides the client's phone ID).

        Returns:
            The sent message.

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
                    tracker=tracker,
                )
            case MessageType.DOCUMENT:
                return self._client.send_document(
                    sender=sender,
                    to=to,
                    document=self.document.id,
                    filename=self.document.filename,
                    caption=body or self.caption,
                    buttons=buttons,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.IMAGE:
                return self._client.send_image(
                    sender=sender,
                    to=to,
                    image=self.image.id,
                    caption=body or self.caption,
                    buttons=buttons,
                    footer=footer,
                    reply_to_message_id=reply_to_message_id,
                    tracker=tracker,
                )
            case MessageType.VIDEO:
                return self._client.send_video(
                    sender=sender,
                    to=to,
                    video=self.video.id,
                    caption=body or self.caption,
                    buttons=buttons,
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
                    sender=sender,
                    to=to,
                    audio=self.audio.id,
                    tracker=tracker,
                    is_voice=self.audio.voice,
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
            case _:
                raise ValueError(f"Message of type {self.type} cannot be copied.")

    def pin(self, *, expiration_days: datetime.timedelta | int) -> SentMessage:
        """
        Pin the message in the chat.

        - Note that currently only group chats support pinning messages.
        - Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/groups/groups-messaging#pin-and-unpin-group-message>`_.

        Args:
            expiration_days: The number of days until the pinned message expires. Must be between 1 and 30 days.

        Returns:
            The pinned message.
        """
        return self._client.pin_message(
            chat_id=self.chat.id,
            message_id=self.id,
            expiration_days=expiration_days,
            sender=self.recipient,
        )

    def unpin(self) -> SentMessage:
        """
        Unpin the message from the chat.

        - Note that currently only group chats support pinning messages.
        - Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/groups/groups-messaging#pin-and-unpin-group-message>`_.

        Returns:
            The unpinned message.
        """
        return self._client.unpin_message(
            chat_id=self.chat.id,
            message_id=self.id,
            sender=self.recipient,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class EditedMessage(BaseUserUpdate):
    """
    A message that has been edited.

    Attributes:
        id: The ID of the edit event (not the original message ID).
        original_message_id: The original message ID before the edit.
        type: The type of the edit (See :class:`MessageType`).
        chat: The chat where the message was edited (private or group).
        metadata: The metadata of the message (to which phone number it was sent).
        from_user: The user who edit the message.
        timestamp: The timestamp when the message was edited (in UTC).
        message: The updated version of the message after the edit.
    """

    _msg_cls: ClassVar[Type[Message]] = Message
    type: MessageType
    chat: Chat
    original_message_id: str
    message: Message

    _webhook_field = "messages"
    _messages_field: ClassVar[str] = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> EditedMessage:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            cls._messages_field
        ][0]
        user = client._usr_cls.from_contact(value["contacts"][0], client=client)
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            original_message_id=msg["edit"]["original_message_id"],
            type=MessageType(msg["edit"]["message"]["type"]),
            from_user=user,
            chat=Chat.from_message(msg=msg, user=user),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            metadata=Metadata.from_dict(value["metadata"]),
            message=cls._msg_cls.from_update(client, update, is_edit=True),
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class DeletedMessage(BaseUserUpdate):
    """
    A message that has been deleted (revoked) by a user.

    Attributes:
        id: The ID of the revoke event (not the original message ID).
        original_message_id: The ID of the message that was deleted.
        type: The type of the update (always :class:`MessageType.REVOKE`).
        chat: The chat where the message was deleted (private or group).
        metadata: The metadata of the message (to which phone number it was sent).
        from_user: The user who deleted the message.
        timestamp: The timestamp when the message was deleted (in UTC).
    """

    type: MessageType
    chat: Chat
    original_message_id: str

    _webhook_field = "messages"
    _messages_field: ClassVar[str] = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> DeletedMessage:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            cls._messages_field
        ][0]
        user = client._usr_cls.from_contact(value["contacts"][0], client=client)
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            original_message_id=msg["revoke"]["original_message_id"],
            type=MessageType.REVOKE,
            from_user=user,
            chat=Chat.from_message(msg=msg, user=user),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]), datetime.timezone.utc
            ),
            metadata=Metadata.from_dict(value["metadata"]),
        )


class _Outgoing:
    from_user: User

    @property
    def to_user(self) -> User:
        """The recipient of the message."""
        return self.from_user


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class OutgoingMessage(_Outgoing, Message):
    """
    A message that is sent by the business (Also known as `Echo message`).

    Attributes:
        id: The message ID (If you want to reply to the message, use ``message_id_to_reply`` instead).
        metadata: The metadata of the message (which phone number was sent from).
        type: The message type (See :class:`MessageType`).
        to_user: The recipient of the message.
        chat: The chat where the message was sent to (private or group).
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this message is a reply (if any).
        forwarded: Whether the message was forwarded.
        forwarded_many_times: Whether the message was forwarded more than 5 times. (when ``True``, ``forwarded`` will be ``True`` as well)
        text: The text of the message.
        image: The image of the message.
        video: The video of the message.
        sticker: The sticker of the message.
        document: The document of the message.
        audio: The audio of the message.
        voice: The voice note of the message (shorthand for ``audio`` if it's a voice note).
        caption: The caption of the message media (Optional, only available for image video and document messages).
        reaction: The reaction of the message.
        location: The location of the message.
        contacts: The contacts of the message.
        order: The order of the message.
        unsupported: The unsupported content of the message.
        error: The error of the message.
        shared_data: Shared data between handlers.
    """

    _webhook_field = "smb_message_echoes"
    _messages_field = "message_echoes"


class OutgoingEditedMessage(_Outgoing, EditedMessage):
    """
    An edited message that is sent by the business (Also known as `Echo message`).

    Attributes:
        id: The ID of the edit event (not the original message ID).
        original_message_id: The original message ID before the edit.
        type: The type of the edit (See :class:`MessageType`).
        chat: The chat where the message was edited (private or group).
        metadata: The metadata of the message (to which phone number it was sent).
        to_user: The recipient of the message.
        timestamp: The timestamp when the message was edited (in UTC).
        message: The updated version of the message after the edit.
    """

    _msg_cls: ClassVar[Type[OutgoingMessage]] = OutgoingMessage
    _webhook_field = "smb_message_echoes"
    _messages_field = "message_echoes"


class OutgoingDeletedMessage(_Outgoing, DeletedMessage):
    """
    A deleted message that is sent by the business (Also known as `Echo message`).

    Attributes:
        id: The ID of the revoke event (not the original message ID).
        original_message_id: The ID of the message that was deleted.
        type: The type of the update (always :class:`MessageType.REVOKE`).
        chat: The chat where the message was deleted (private or group).
        metadata: The metadata of the message (to which phone number it was sent).
        to_user: The recipient of the message.
        timestamp: The timestamp when the message was deleted (in UTC).
    """

    _webhook_field = "smb_message_echoes"
    _messages_field = "message_echoes"
