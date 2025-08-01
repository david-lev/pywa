from __future__ import annotations

from typing import cast

from pywa.types.sent_update import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.sent_update import (
    SentMessage as _SentMessage,
    SentTemplate as _SentTemplate,
    InitiatedCall as _InitiatedCall,
)
from pywa_async.types import (
    Message,
    CallbackButton,
    CallbackSelection,
    MessageStatus,
    FlowCompletion,
)
from .calls import _CallShortcutsAsync

from .. import filters as pywa_filters

__all__ = ["SentMessage", "SentTemplate", "SentTemplateStatus", "InitiatedCall"]

from pywa_async.types.base_update import _ClientShortcutsAsync


class SentMessage(_ClientShortcutsAsync, _SentMessage):
    """
    Represents a message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
    """

    async def wait_for_reply(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=filters,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    async def wait_until_read(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.message_status & pywa_filters.read,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    async def wait_until_delivered(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.message_status & pywa_filters.delivered,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    async def wait_for_click(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.callback_button
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    async def wait_for_selection(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.callback_selection
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )

    async def wait_for_completion(
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
            await self._client.listen(
                to=self.listener_identifier,
                filters=pywa_filters.flow_completion
                & (pywa_filters.replays_to(self.id) & (filters or pywa_filters.true)),
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


class SentTemplate(SentMessage, _SentTemplate):
    """
    Represents a template message that was sent to WhatsApp user.

    Attributes:
        id: The ID of the message.
        to_user: The user the message was sent to.
        from_phone_id: The WhatsApp ID of the sender who sent the message.
        status: The status of the sent template.
    """


class InitiatedCall(_CallShortcutsAsync, _ClientShortcutsAsync, _InitiatedCall):
    """
    Represents an outgoing call initiated by the business.

    Attributes:
        id: The call ID.
        to_user: The user to whom the call was made.
        from_phone_id: The WhatsApp ID of the business phone number that initiated the call.
        success: Whether the call was successfully initiated.
    """
