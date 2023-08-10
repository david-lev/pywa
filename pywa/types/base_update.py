from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, TYPE_CHECKING, BinaryIO
from .others import MessageType, Metadata, User, Contact

if TYPE_CHECKING:
    from pywa.client import WhatsApp
    from .callback import InlineButton, SectionList


@dataclass(frozen=True, slots=True)
class BaseUpdate:
    """Base class for all update types."""
    _client: WhatsApp = field(repr=False, hash=False, compare=False)
    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime

    @property
    def sender(self) -> str:
        return self.from_user.wa_id

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to."""
        return self.id

    def reply_text(
            self,
            text: str,
            preview_url: bool = False,
            quote: bool = False,
            keyboard: list[InlineButton] | SectionList | None = None,
            header: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with text.

        Args:
            text: The text to reply with.
            preview_url: Whether to show a preview of the URL in the text (default: False).
            quote: Whether to quote the message (default: False).
            keyboard: The keyboard to send with the message (optional).
            header: The header of the message (if keyboard is provided, optional, up to 60 characters, no markdown allowed).
            footer: The footer of the message (if keyboard is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_message(
            to=self.sender,
            text=text,
            preview_url=preview_url,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            keyboard=keyboard,
            header=header,
            footer=footer
        )

    def reply_image(
            self,
            image: str | bytes | BinaryIO,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with an image.

        Args:
            image: The image to reply with.
            caption: The caption of the image (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_image(
            to=self.sender,
            image=image,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_video(
            self,
            video: str | bytes | BinaryIO,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with a video.

        Args:
            video: The video to reply with.
            caption: The caption of the video (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_video(
            to=self.sender,
            video=video,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_document(
            self,
            document: str | bytes | BinaryIO,
            filename: str | None = None,
            caption: str | None = None,
            quote: bool = False,
            buttons: list[InlineButton] | None = None,
            body: str | None = None,
            footer: str | None = None,
    ) -> str:
        """
        Reply to the message with a document.

        Args:
            document: The document to reply with.
            filename: The filename of the document (optional, The extension of the filename will specify what format the document is displayed as in WhatsApp).
            caption: The caption of the document (optional).
            quote: Whether to quote the message (default: False).
            buttons: The buttons to send with the message (optional).
            body: The body of the message (if buttons is provided, optional).
            footer: The footer of the message (if buttons is provided, optional, up to 60 characters, markdown has no effect).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_document(
            to=self.sender,
            document=document,
            filename=filename,
            caption=caption,
            reply_to_message_id=self.message_id_to_reply if quote else None,
            buttons=buttons,
            body=body,
            footer=footer
        )

    def reply_audio(
            self,
            audio: str | bytes | BinaryIO,
    ) -> str:
        """
        Reply to the message with an audio.

        Args:
            audio: The audio to reply with.

        Returns:
            The ID of the sent message.
        """
        return self._client.send_audio(
            to=self.sender,
            audio=audio,
        )

    def reply_sticker(
            self,
            sticker: str | bytes | BinaryIO,
    ) -> str:
        """
        Reply to the message with a sticker.

        Args:
            sticker: The sticker to reply with.

        Returns:
            The ID of the sent message.
        """
        return self._client.send_sticker(
            to=self.sender,
            sticker=sticker,
        )

    def reply_location(
            self,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ) -> str:
        """
        Reply to the message with a location.

        Args:
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location (optional).
            address: The address of the location (optional).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_location(
            to=self.sender,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address
        )

    def reply_contact(
            self,
            contact: Contact | Iterable[Contact],
            quote: bool = False,
    ) -> str:
        """
        Reply to the message with a contact.

        Args:
            contact: The contact/s to send.
            quote: Whether to quote the message (default: False).

        Returns:
            The ID of the sent message.
        """
        return self._client.send_contact(
            to=self.sender,
            contact=contact,
            reply_to_message_id=self.message_id_to_reply if quote else None
        )

    def react(
            self,
            emoji: str,
    ) -> str:
        """
        React to the message with an emoji.

        Args:
            emoji: The emoji to react with.

        Returns:
            The ID of the sent message.
        """
        return self._client.send_reaction(
            to=self.sender,
            emoji=emoji,
            message_id=self.message_id_to_reply
        )

    def unreact(
            self,
    ) -> str:
        """
        Remove the reaction from the message.

        Returns:
            The ID of the sent message.
        """
        return self._client.remove_reaction(
            to=self.sender,
            message_id=self.message_id_to_reply
        )

    def mark_as_read(
            self
    ) -> bool:
        """
        Mark the message as read.

        Returns:
            Whether it was successful.
        """
        return self._client.mark_message_as_read(
            message_id=self.message_id_to_reply
        )
