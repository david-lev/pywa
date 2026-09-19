"""This module contains the types related to message status updates."""

from __future__ import annotations

__all__ = [
    "Conversation",
    "ConversationCategory",
    "MessageStatus",
    "MessageStatusType",
    "Pricing",
    "PricingCategory",
    "PricingModel",
    "PricingType",
]

from pywa.types.message_status import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.message_status import MessageStatus as _MessageStatus

from pywa.types.message_status import User as _User
from .user import BaseUserAsync
from .base_update import BaseUserUpdateAsync
from .callback import _CallbackDataT


class User(BaseUserAsync, _User):
    """
    Represents the WhatsApp user a :class:`MessageStatus` was sent to.

    Attributes:
        bsuid: The WhatsApp user’s BSUID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids>`_ for more information. Will be ``None`` if the message status is ``FAILED`` because the user has no WhatsApp account.
        wa_id: The user's phone number in international format (without the '+' sign). Will be unavailable if the user enables the username feature. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#phone-numbers>`_ for more information.
        name: The name of the user.
        username: The username of the user.
        identity_key_hash: The identity key hash of the user (Only if identity key check is enabled on the phone number settings).
        parent_bsuid: The Parent business-scoped user ID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#parent-business-scoped-user-ids>`_ for more information.
    """


class MessageStatus(BaseUserUpdateAsync, _MessageStatus[_CallbackDataT]):
    """
    Represents the status of a message.

    - `'MessageStatus' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object>`_.

    ``MessageStatus`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``tracker`` attribute.

    Here is an example:

        >>> from pywa_async.types import CallbackData
        >>> import dataclasses  # Use dataclass to get free ordered __init__
        >>> @dataclasses.dataclass(frozen=True, slots=True) # Do not use kw_only=True
        >>> class UserData(CallbackData):  # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa_async import WhatsApp
        >>> from pywa_async.types import Button, CallbackButton
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to="972987654321",
        ...     text="Hi user",
        ...     tracker=UserData(
        ...         id=123, name="david", admin=True
        ...     ),  # Here ^^^ we use the UserData class as the tracker
        ... )  # Here ^^^ we use the UserData class as the tracker data

        >>> @wa.on_message_status(
        ...     factory=UserData
        ... )  # Use the factory parameter to convert the tracker data
        ... def on_status(_: WhatsApp, s: MessageStatus[UserData]):  # For autocomplete
        ...     if s.tracker.admin:
        ...         print(s.tracker.id)  # Access the tracker data



    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated (in UTC).
        from_user: The user who the message was sent to. The user may not have a WhatsApp account, in which case the ``bsuid`` attribute will be ``None``.
        conversation: The conversation that the message was sent in (See `Conversation <https://developers.facebook.com/docs/whatsapp/pricing#conversations>`_).
        pricing: The pricing of the message (Optional).
        error: The error that occurred (if status is :class:`MessageStatusType.FAILED`).
        tracker: The tracker that the message was sent with (e.g. ``wa.send_message(tracker=...)``).
        shared_data: Shared data between handlers.
    """

    from_user: User
    _usr_cls = User
