from __future__ import annotations

__all__ = ["SentMessage", "SentTemplate", "SentTemplateStatus", "InitiatedCall"]

import abc
import dataclasses

from typing import TYPE_CHECKING, cast
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
)
from pywa.types.base_update import _ClientShortcuts, BaseUpdate, BaseUserUpdate
from pywa.types.calls import _CallShortcuts

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
            sender=self.sender, recipient=self.recipient
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SentMessage(_SentUpdate):
    """
    Represents a message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
    """

    _callback_options: set[str] | None = dataclasses.field(
        repr=False, hash=False, compare=False, default=None
    )  # TODO need this?
    _flow_token: str | None = dataclasses.field(
        repr=False, hash=False, compare=False, default=None
    )

    @classmethod
    def from_sent_update(
        cls, *, client: WhatsApp, update: dict, from_phone_id: str, **kwargs
    ) -> SentMessage:
        msg_id, user = (
            update["messages"][0]["id"],
            client._usr_cls.from_dict(update["contacts"][0], client=client),
        )
        return cls(
            _client=client,
            id=msg_id,
            to_user=user,
            from_phone_id=from_phone_id,
            **kwargs,
        )

    def wait_for_reply(
        self,
        *,
        force_quote: bool = False,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
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
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the message to be read.

        Returns:
            The message status.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
        if cancel_on_new_update:
            new_update_canceler = ~pywa_filters.update_id(self.id) & (
                pywa_filters.message
                | pywa_filters.callback_button
                | pywa_filters.callback_selection
            )
            cancelers = (
                (new_update_canceler & cancelers) if cancelers else new_update_canceler
            )
        return cast(
            MessageStatus,
            self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.message_status & pywa_filters.read,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_until_delivered(
        self,
        *,
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
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the message to be delivered.

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
                filters=pywa_filters.message_status & pywa_filters.delivered,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    def wait_for_click(
        self,
        *,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
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
            timeout: The time to wait for the button click.

        Returns:
            The clicked button.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
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
        timeout: float | None = None,
    ) -> CallbackSelection:
        """
        Wait for a callback selection.

        Args:
            filters: The filters to apply to the selection.
            cancelers: The filters to cancel the listening.
            timeout: The time to wait for the selection.

        Returns:
            The callback selection.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """

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
            timeout: The time to wait for the completion.

        Returns:
            The flow completion.

        Raises:
            ListenerTimeout: If the listener timed out.
            ListenerCanceled: If the listener was canceled by a filter.
            ListenerStopped: If the listener was stopped manually.
        """
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


class SentTemplateStatus(utils.StrEnum):
    """
    Represents the status of a sent template.

    - Read more about template pacing on `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#template-pacing>`_.

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
            **kwargs,
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
