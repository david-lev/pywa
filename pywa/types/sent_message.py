from __future__ import annotations

__all__ = ["SentMessage"]

import dataclasses

from typing import TYPE_CHECKING
from pywa import filters as pywa_filters
from pywa.types import (
    CallbackButton,
    User,
    Message,
    MessageStatus,
    CallbackSelection,
    FlowCompletion,
)
from pywa.types.base_update import _ClientShortcuts

if TYPE_CHECKING:
    from pywa import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SentMessage(_ClientShortcuts):
    """
    Represents a message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _callback_options: set[str] | None = dataclasses.field(
        repr=False, hash=False, compare=False, default=None
    )
    _flow_token: str | None = dataclasses.field(
        repr=False, hash=False, compare=False, default=None
    )
    id: str
    to_user: User
    from_phone_id: str

    @property
    def recipient(self) -> str:
        """
        The WhatsApp ID which the message was sent to.
            - Shortcut for ``.to_user.wa_id``.
        """
        return self.to_user.wa_id

    @property
    def _internal_recipient(self) -> str:
        return self.sender

    @property
    def sender(self) -> str:
        """
        The WhatsApp ID of the sender who sent the message.
            - Same as ``.from_phone_id``.
        """
        return self.from_phone_id

    @property
    def _internal_sender(self) -> str:
        return self.recipient

    @classmethod
    def from_sent_update(
        cls, *, client: WhatsApp, update: dict, from_phone_id: str, **kwargs
    ) -> SentMessage:
        msg_id, user = (
            update["messages"][0]["id"],
            User(update["contacts"][0]["wa_id"], name=None),
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
        force_quote: bool = False,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
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
                        filters=filters.text,
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
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=filters,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_until_read(
        self,
        cancel_on_new_update: bool = False,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
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
            cancel_on_new_update: Whether to cancel when another user update arrives (which may indicate the previous message was read).
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
            new_update_canceler = ~pywa_filters.update_id(self.id)
            cancelers = (
                (new_update_canceler & cancelers) if cancelers else new_update_canceler
            )
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=pywa_filters.update_id(self.id) & pywa_filters.read,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_until_delivered(
        self,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
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

        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=pywa_filters.update_id(self.id) & pywa_filters.delivered,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_for_click(
        self,
        force_options: bool = True,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
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
            force_options: Whether to force the button to be one of the sent buttons.
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
        if force_options:
            if not self._callback_options:
                raise ValueError("No callback options available to wait for")
            contains_filter = pywa_filters.new(
                lambda _, c: c.data in self._callback_options
            )
            filters = (contains_filter & filters) if filters else contains_filter
        filters = (
            (pywa_filters.callback_button & filters)
            if filters
            else pywa_filters.callback_button
        )

        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=filters,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_for_selection(
        self,
        force_options: bool = True,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
    ) -> CallbackSelection:
        """
        Wait for a callback selection.

        Args:
            force_options: Whether to force the selection to be one of the sent rows.
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
        if force_options:
            if not self._callback_options:
                raise ValueError("No callback options available to wait for")
            contains_filter = pywa_filters.new(
                lambda _, c: c.data in self._callback_options
            )
            filters = (contains_filter & filters) if filters else contains_filter
        filters = (
            (pywa_filters.callback_selection & filters)
            if filters
            else pywa_filters.callback_selection
        )
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=filters,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_for_completion(
        self,
        force_token: bool = True,
        filters: pywa_filters.Filter = None,
        cancelers: pywa_filters.Filter = None,
        timeout: int | None = None,
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
            force_token: Whether to force the completion to have the sent token.
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
        if force_token:
            if not self._flow_token:
                raise ValueError("No flow token available to wait for")
            token_filter = pywa_filters.new(lambda _, c: c.token == self._flow_token)
            filters = (token_filter & filters) if filters else token_filter
        filters = (
            (pywa_filters.flow_completion & filters)
            if filters
            else pywa_filters.flow_completion
        )
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=filters,
            cancelers=cancelers,
            timeout=timeout,
        )
