from __future__ import annotations

__all__ = [
    "SentMessage",
    "SentMediaMessage",
    "SentVoiceMessage",
    "SentLocationRequest",
    "SentTemplate",
    "SentTemplateStatus",
    "InitiatedCall",
]

import abc
import dataclasses

from typing import TYPE_CHECKING, cast, TypeVar
from pywa import filters as pywa_filters, utils
from pywa.listeners import UserUpdateListenerIdentifier
from pywa.types import (
    CallbackButton,
    User,
    Message,
    MessageStatus,
    CallbackSelection,
    FlowCompletion,
    Button,
    URLButton,
    VoiceCallButton,
    SectionList,
    FlowButton,
    CallbackData,
    CallStatus,
    MessageStatusType,
)
from pywa.types.base_update import _ClientShortcuts, BaseUpdate, BaseUserUpdate
from pywa.types.calls import _CallShortcuts
from pywa.types.media import Media

if TYPE_CHECKING:
    from pywa import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _SentUpdate(_ClientShortcuts, abc.ABC):
    """
    Base class for sent updates, providing common attributes and methods.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    to_user: User
    from_phone_id: str

    @property
    def recipient(self) -> str:
        """
        The recipient's WhatsApp ID.
        """
        return self._internal_sender

    @property
    def sender(self) -> str:
        """
        The sender's WhatsApp ID.
        """
        return self._internal_recipient

    @property
    def _internal_recipient(self) -> str:
        return self.from_phone_id

    @property
    def _internal_sender(self) -> str:
        return self.to_user.wa_id

    @classmethod
    @abc.abstractmethod
    def from_sent_update(cls, *args, **kwargs) -> _SentUpdate: ...

    @property
    def listener_identifier(self) -> UserUpdateListenerIdentifier:
        return UserUpdateListenerIdentifier(
            sender=self.recipient, recipient=self.sender
        )


def _ignore_updates_canceler(_, u: BaseUserUpdate) -> bool:
    if u._is_user_action:
        u.stop_handling()
    return False


def _failed_canceler(_, u: BaseUserUpdate) -> bool:
    if isinstance(u, MessageStatus) and u.status == MessageStatusType.FAILED:
        return True
    return False


def _new_update_canceler(_, u: BaseUserUpdate) -> bool:
    if u._is_user_action:
        return True
    return False


ignore_updates_canceler = pywa_filters.new(_ignore_updates_canceler)
failed_canceler = pywa_filters.new(_failed_canceler)
new_update_canceler = pywa_filters.new(_new_update_canceler)


_SentMessageType = TypeVar("_SentMessageType", bound="SentMessage")


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SentMessage(_SentUpdate):
    """
    Represents a message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        input: The input (phone number) of the recipient.
    """

    input: str

    @classmethod
    def from_sent_update(
        cls, *, client: WhatsApp, update: dict, from_phone_id: str, **kwargs
    ) -> SentMessage:
        msg_id, user = (
            update["messages"][0]["id"],
            client._usr_cls.from_dict(update["contacts"][0], client=client),
        )
        # noinspection PyArgumentList
        return cls(
            _client=client,
            id=msg_id,
            to_user=user,
            from_phone_id=from_phone_id,
            input=update["contacts"][0]["input"],
            **kwargs,
        )

    def _convert_to(self, subclass: type[_SentMessageType]) -> _SentMessageType:
        return subclass(
            _client=self._client,
            id=self.id,
            to_user=self.to_user,
            from_phone_id=self.from_phone_id,
            input=self.input,
        )

    def wait_for_reply(
        self,
        *,
        force_quote: bool = False,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        ignore_updates: bool = True,
        timeout: float | None = None,
    ) -> Message:
        """
        Wait for a message reply to the sent message.

        - Shortcut for :meth:`~pywa.client.WhatsApp.listen` with ``filters=filters.message``.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    user_id: str = m.reply(
                        text=f"Hi {m.from_user.name}! Please enter your ID",
                        buttons=[Button(title="Cancel", callback_data="cancel")],
                    ).wait_for_reply(
                        filters=filters.text & filters.new(lambda _, m: m.text.isdigit()),
                        cancelers=filters.callback_button & filters.matches("cancel"),
                    ).text
                    ...
        Args:
            force_quote: Whether to force the reply to quote the sent message.
            filters: The filters to apply to the reply.
            cancelers: The filters to cancel the listening.
            ignore_updates: Whether to ignore user updates that do not pass the filters.
            timeout: The time to wait for a reply.

        Returns:
            The reply message.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if force_quote:
            reply_filter = pywa_filters.replays_to(self.id)
            filters = (reply_filter & filters) if filters else reply_filter
        filters = (pywa_filters.message & filters) if filters else pywa_filters.message
        if ignore_updates:
            cancelers = (
                (cancelers | ignore_updates_canceler)
                if cancelers
                else ignore_updates_canceler
            )

        return cast(
            Message,
            self._client.listen(
                to=self.listener_identifier,
                filters=filters,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_until_read(
        self,
        *,
        cancel_on_new_update: bool = False,
        cancel_if_failed: bool = True,
        cancelers: pywa_filters.Filter = None,
        timeout: float | None = None,
    ) -> MessageStatus:
        """
        Wait for the message to be read by the recipient.

        - Shortcut for :meth:`~pywa.client.WhatsApp.listen` with ``filters=filters.message_status & filters.read``.

        **Note:** This method will not work if the recipient has disabled read receipts.
        make sure to use ``cancel_on_new_update=True`` to cancel the listening if the message is probably read, or use a timeout / cancelers.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    r = m.reply("This message waits for you to read it")
                    try:
                        r.wait_until_read(cancel_on_new_update=True)
                    except ListenerCanceled as e:
                        print(e.update) # The update that canceled the listener
                        r.reply("You turned off read receipts")
                    r.reply("You read this message", quote=True)

        Args:
            cancel_on_new_update: Whether to cancel when another message/button click arrives (which may indicate the previous message was read).
            cancel_if_failed: Whether to cancel the listener if the message failed to send.
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the message to be read.

        Returns:
            The message status.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if cancel_if_failed:
            cancelers = (cancelers | failed_canceler) if cancelers else failed_canceler
        if cancel_on_new_update:
            cancelers = (
                (cancelers | new_update_canceler) if cancelers else new_update_canceler
            )
        return cast(
            MessageStatus,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.update_id(self.id) & pywa_filters.read,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_until_delivered(
        self,
        *,
        cancel_if_failed: bool = True,
        cancelers: pywa_filters.Filter = None,
        timeout: float | None = None,
    ) -> MessageStatus:
        """
        Wait for the message to be delivered to the recipient.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    r = m.reply("This message waits for you to receive it")
                    r.wait_until_delivered()
                    r.reply("You received the message", quote=True)

        Args:
            cancel_if_failed: Whether to cancel the listener if the message failed to send.
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the message to be delivered.

        Returns:
            The message status.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if cancel_if_failed:
            cancelers = (cancelers | failed_canceler) if cancelers else failed_canceler
        return cast(
            MessageStatus,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.update_id(self.id)
                & (pywa_filters.read | pywa_filters.delivered),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_until_failed(
        self,
        *,
        cancel_if_delivered: bool = True,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: float | None = None,
    ) -> MessageStatus:
        """
        Wait for the message to fail.

        Example:

            .. code-block:: python

                m = wa.send_message(
                    to="123456",
                    text="This message will fail",
                )
                try:
                    failed = m.wait_for_failed(
                        filters=filters.failed_with(errors.ReEngagementMessage),  # message was send after 24 hours
                        cancel_if_delivered=True, # defaults to True, so the listener will be canceled if the message was delivered
                        timeout=5,
                    )
                    failed.reply_template(...)
                except ListenerCanceled:
                    print("The message was delivered successfully, so the listener was canceled.")
                except ListenerTimeout:
                    pass

        Args:
            filters: The filters to apply to the failed message.
            cancel_if_delivered: Whether to cancel the listener if the message was delivered.
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the message to fail.

        Returns:
            The message status indicating the failure.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if cancel_if_delivered:
            cancelers = (
                (cancelers | pywa_filters.delivered)
                if cancelers
                else pywa_filters.delivered
            )
        return cast(
            MessageStatus,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.message_status
                & pywa_filters.failed
                & (filters or pywa_filters.true),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_for_click(
        self,
        *,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        ignore_updates: bool = True,
        timeout: float | None = None,
    ) -> CallbackButton:
        """
        Wait for a button click.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    r = m.reply(
                        text="Click a button",
                        buttons=[
                            Button(title="Option 1", callback_data="option1"),
                            Button(title="Option 2", callback_data="option2"),
                        ],
                    )
                    option = r.wait_for_click()
                    r.reply(f"You clicked: {option.title}", quote=True)

        Args:
            filters: The filters to apply to the button click.
            cancelers: The filters to cancel the listening.
            ignore_updates: Whether to ignore user updates that do not pass the filters.
            timeout: The time to wait for the button click.

        Returns:
            The clicked button.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if ignore_updates:
            cancelers = (
                (cancelers | ignore_updates_canceler)
                if cancelers
                else ignore_updates_canceler
            )
        return cast(
            CallbackButton,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.callback_button
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_for_selection(
        self,
        *,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        ignore_updates: bool = True,
        timeout: float | None = None,
    ) -> CallbackSelection:
        """
        Wait for a callback selection.

        Args:
            filters: The filters to apply to the selection.
            cancelers: The filters to cancel the listening.
            ignore_updates: Whether to ignore user updates that do not pass the filters.
            timeout: The time to wait for the selection.

        Returns:
            The callback selection.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if ignore_updates:
            cancelers = (
                (cancelers | ignore_updates_canceler)
                if cancelers
                else ignore_updates_canceler
            )
        return cast(
            CallbackSelection,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.callback_selection
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_for_completion(
        self,
        *,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        ignore_updates: bool = True,
        timeout: float | None = None,
    ) -> FlowCompletion:
        """
        Wait for a flow completion.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    flow_completion = m.reply(
                        text="Answer the questions",
                        buttons=FlowButton(flow_token=..., ...),
                    ).wait_for_completion()

        Args:
            filters: The filters to apply to the completion.
            cancelers: The filters to cancel the listening.
            ignore_updates: Whether to ignore user updates that do not pass the filters.
            timeout: The time to wait for the completion.

        Returns:
            The flow completion.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if ignore_updates:
            cancelers = (
                (cancelers | ignore_updates_canceler)
                if cancelers
                else ignore_updates_canceler
            )
        return cast(
            FlowCompletion,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.flow_completion
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SentMediaMessage(SentMessage):
    """
    Represents a media message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        input: The input (phone number) of the recipient.
        uploaded_media: The media that was uploaded and sent in the message (only available if the media was not Media ID or URL).
    """

    uploaded_media: Media | None = None


class SentVoiceMessage(SentMediaMessage):
    """
    Represents a voice message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        input: The input (phone number) of the recipient.
        uploaded_media: The media that was uploaded and sent in the message (only available if the media was not Media ID or URL).
    """

    def wait_until_played(
        self,
        *,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: float | None = None,
    ) -> MessageStatus:
        """
        Wait for the voice message to be played by the recipient.

        Example:

            .. code-block:: python

                @wa.on_message(filters.command("start"))
                def start(w: WhatsApp, m: Message):
                    r = m.reply_voice(
                        voice_url="https://example.com/voice.mp3",
                    )
                    r.wait_until_played()
                    r.reply("You played the voice message", quote=True)

        Args:
            filters: The filters to apply to the played status.
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the voice message to be played.

        Returns:
            The message status.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        return cast(
            MessageStatus,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.update_id(self.id)
                & pywa_filters.played
                & (filters or pywa_filters.true),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


class SentLocationRequest(SentMessage):
    """
    Represents a location request message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        input: The input (phone number) of the recipient.
    """

    def wait_for_location(
        self,
        *,
        force_current_location: bool = True,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        ignore_updates: bool = True,
        timeout: float | None = None,
    ) -> Message:
        """
        Wait for a location message in response to the location request.

        Args:
            force_current_location: Whether to only accept current location messages.
            filters: The filters to apply to the location message.
            cancelers: The filters to cancel the listening.
            ignore_updates: Whether to ignore user updates that do not pass the filters.
            timeout: The time to wait for the location message.

        Returns:
            The location message.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if ignore_updates:
            cancelers = (
                (cancelers | ignore_updates_canceler)
                if cancelers
                else ignore_updates_canceler
            )
        return cast(
            Message,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.message
                & (
                    pywa_filters.current_location
                    if force_current_location
                    else pywa_filters.location
                )
                & (filters or pywa_filters.true),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


class SentTemplateStatus(utils.StrEnum):
    """
    Represents the status of a sent template.

    - Read more about template pacing on `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-pacing>`_.

    Attributes:
        ACCEPTED: The template was accepted.
        HELD_FOR_QUALITY_ASSESSMENT: The template was held for quality assessment.
    """

    _check_value = str.islower
    _modify_value = str.lower

    ACCEPTED = "accepted"
    HELD_FOR_QUALITY_ASSESSMENT = "held_for_quality_assessment"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SentTemplate(SentMessage):
    """
    Represents a template message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        status: The status of the sent template.
        input: The input (phone number) of the recipient.
    """

    status: SentTemplateStatus | None

    @classmethod
    def from_sent_update(
        cls, *, client: WhatsApp, update: dict, from_phone_id: str, **kwargs
    ) -> SentTemplate:
        msg, user = (
            update["messages"][0],
            client._usr_cls.from_dict(update["contacts"][0], client=client),
        )
        return cls(
            _client=client,
            id=msg["id"],
            status=SentTemplateStatus(msg["message_status"])
            if "message_status" in msg
            else None,
            to_user=user,
            from_phone_id=from_phone_id,
            input=update["contacts"][0]["input"],
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class InitiatedCall(_SentUpdate, _CallShortcuts):
    """
    Represents an outgoing call initiated by the business.

    Attributes:
        id: The call ID.
        to_user: The user to whom the call was made.
        from_phone_id: The WhatsApp ID of the business phone number that initiated the call.
        success: Whether the call was successfully initiated.
    """

    success: bool

    @classmethod
    def from_sent_update(
        cls, client: WhatsApp, update: dict, from_phone_id: str, to_wa_id: str
    ) -> InitiatedCall:
        return cls(
            _client=client,
            id=update["calls"][0]["id"],
            to_user=client._usr_cls(_client=client, wa_id=to_wa_id, name=None),
            from_phone_id=from_phone_id,
            success=update["success"],
        )
