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
            - Shortcut for ``.metadata.phone_number_id``.
        """
        return self.to_user.wa_id

    @property
    def sender(self) -> str:
        """
        The WhatsApp ID of the sender who sent the message.
            - Shortcut for ``.from_user.wa_id``.
        """
        return self.from_phone_id

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
        filters: pywa_filters.Filter | None = None,
        cancelers: pywa_filters.Filter | None = None,
        timeout: int | None = None,
    ) -> Message:
        """
        Wait for a reply to the sent message.

        Example:

            .. code-block:: python

                @wa.on_message(filters.text.command("start"))
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
        """
        if force_quote:
            reply_filter = pywa_filters.replays_to(self.id)
            filters = (reply_filter & filters) if filters else reply_filter
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=pywa_filters.message & filters,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_to_read(
        self,
        cancel_when_delivered: bool = False,
        cancelers: pywa_filters.Filter | None = None,
        timeout: int | None = None,
    ) -> MessageStatus:
        if cancel_when_delivered:
            delivered_canceler = (
                pywa_filters.message_status & pywa_filters.message_status.delivered
            )
            cancelers = (
                (delivered_canceler & cancelers) if cancelers else delivered_canceler
            )
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=pywa_filters.message_status & pywa_filters.message_status.read,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_to_delivered(
        self,
        cancel_when_read: bool = True,
        cancelers: pywa_filters.Filter | None = None,
        timeout: int | None = None,
    ) -> MessageStatus:
        if cancel_when_read:
            read_canceler = (
                pywa_filters.message_status & pywa_filters.message_status.read
            )
            cancelers = (read_canceler & cancelers) if cancelers else read_canceler
        return self._client.listen(
            to=self.recipient,
            sent_to_phone_id=self.sender,
            filters=pywa_filters.message_status & pywa_filters.message_status.delivered,
            cancelers=cancelers,
            timeout=timeout,
        )

    def wait_for_click(self) -> CallbackButton: ...

    def wait_for_selection(self) -> CallbackSelection: ...

    def wait_for_completion(self) -> FlowCompletion: ...
