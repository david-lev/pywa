"""This module contains the types related to message status updates."""

from __future__ import annotations

from .callback import _CallbackDataT

__all__ = [
    "MessageStatus",
    "MessageStatusType",
    "Conversation",
    "ConversationCategory",
    "Pricing",
    "PricingModel",
    "PricingType",
    "PricingCategory",
]

import dataclasses
import datetime
import logging
from typing import TYPE_CHECKING, Generic

from .. import utils
from ..errors import WhatsAppError
from .base_update import BaseUserUpdate, RawUpdate  # noqa
from .others import Metadata

if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)


class MessageStatusType(utils.StrEnum):
    """
    Message status type.

    Attributes:
        SENT: Indicates the message was successfully sent from our servers (WhatsApp UI equivalent: One checkmark).
        DELIVERED: Indicates message was successfully delivered to the WhatsApp user's device (WhatsApp UI equivalent: Two checkmarks).
        READ: Indicates the message was displayed in an open chat thread in the WhatsApp user's device (WhatsApp UI equivalent: Two blue checkmarks).
        PLAYED: played — Indicates the first time a voice message is played to the WhatsApp user's device (WhatsApp UI equivalent: Blue microphone).
        FAILED: failed — Indicates failure to send or deliver the message to the WhatsApp user's device (WhatsApp UI equivalent: Red error triangle).
    """

    _check_value = str.islower
    _modify_value = str.lower

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PLAYED = "played"

    UNKNOWN = "UNKNOWN"


class ConversationCategory(utils.StrEnum):
    """
    Conversation category.

    Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/pricing#conversation-categories>`_.

    Attributes:
        AUTHENTICATION: Indicates an authentication conversation.
        AUTHENTICATION_INTERNATIONAL: Indicates an `authentication-international <https://developers.facebook.com/docs/whatsapp/pricing/authentication-international-rates/>`_ conversation.
        MARKETING: Indicates a marketing conversation.
        MARKETING_LITE: Indicates a `Marketing Messages Lite API <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/>`_ conversation.
        UTILITY: Indicates a utility conversation.
        SERVICE: Indicates a service conversation.
        REFERRAL_CONVERSION: Indicates a free entry point conversation.
        UNKNOWN: The conversation category is unknown.
    """

    _check_value = str.islower
    _modify_value = str.lower

    AUTHENTICATION = "authentication"
    AUTHENTICATION_INTERNATIONAL = "authentication_international"
    MARKETING = "marketing"
    MARKETING_LITE = "marketing_lite"
    UTILITY = "utility"
    SERVICE = "service"
    REFERRAL_CONVERSION = "referral_conversion"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class MessageStatus(BaseUserUpdate, Generic[_CallbackDataT]):
    """
    Represents the status of a message.

    - `'MessageStatus' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object>`_.

    ``MessageStatus`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``tracker`` attribute.

    Here is an example:

        >>> from pywa.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa import WhatsApp
        >>> from pywa.types import Button, CallbackButton
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Hi user',
        ...     tracker=UserData(id=123, name='david', admin=True) # Here ^^^ we use the UserData class as the tracker
        ... )           # Here ^^^ we use the UserData class as the tracker data

        >>> @wa.on_message_status(factory=UserData) # Use the factory parameter to convert the tracker data
        ... def on_status(_: WhatsApp, s: MessageStatus[UserData]): # For autocomplete
        ...    if s.tracker.admin: print(s.tracker.id) # Access the tracker data



    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated (in UTC).
        from_user: The user who the message was sent to.
        conversation: The conversation that the message was sent in (See `Conversation <https://developers.facebook.com/docs/whatsapp/pricing#conversations>`_).
        pricing: The pricing of the message (Optional).
        error: The error that occurred (if status is :class:`MessageStatusType.FAILED`).
        tracker: The tracker that the message was sent with (e.g. ``wa.send_message(tracker=...)``).
        shared_data: Shared data between handlers.
    """

    status: MessageStatusType
    pricing: Pricing | None
    conversation: Conversation | None
    error: WhatsAppError | None
    tracker: _CallbackDataT | None

    _txt_fields = ("tracker",)
    _webhook_field = "messages"
    _is_user_action = False

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> MessageStatus:
        status = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "statuses"
        ][0]
        error = value.get("errors", status.get("errors", (None,)))[0]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=status["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            status=MessageStatusType(status["status"]),
            timestamp=datetime.datetime.fromtimestamp(
                int(status["timestamp"]),
                datetime.timezone.utc,
            ),
            from_user=client._usr_cls(
                wa_id=status["recipient_id"],
                identity_key_hash=status.get("recipient_identity_key_hash"),
                name=None,
                _client=client,
            ),
            tracker=status.get("biz_opaque_callback_data"),
            conversation=Conversation.from_dict(status["conversation"])
            if "conversation" in status
            else None,
            pricing=Pricing.from_dict(status["pricing"])
            if "pricing" in status
            else None,
            error=WhatsAppError.from_dict(error=error) if error else None,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Conversation:
    """
    Conversations are 24-hour message threads between you and your customers.
    They are opened and charged when messages you send to customers are delivered.

    - `'Conversation' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/pricing#conversations>`_.

    Attributes:
        id: Represents the ID of the conversation the given status notification belongs to.
        category: The category of the conversation.
        expiration: The expiration date (in UTC) of the conversation (Optional, only for `sent` updates).
    """

    id: str
    category: ConversationCategory
    expiration: datetime.datetime | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            category=ConversationCategory(data["origin"]["type"]),
            expiration=datetime.datetime.fromtimestamp(
                int(data["expiration_timestamp"]),
                datetime.timezone.utc,
            )
            if "expiration_timestamp" in data
            else None,
        )


class PricingModel(utils.StrEnum):
    """
    Pricing model.

    Attributes:
        CBP: Indicates conversation-based pricing applies. Will only be set to this value if the webhook was sent before July 1, 2025.
        PMP: Indicates `per-message pricing <https://developers.facebook.com/docs/whatsapp/pricing>`_ applies.
    """

    CBP = "CBP"
    PMP = "PMP"

    UNKNOWN = "UNKNOWN"


class PricingType(utils.StrEnum):
    """
    Pricing type.

    Attributes:
        REGULAR: Indicates the message is billable.
        FREE_CUSTOMER_SERVICE: Indicates the message is free because it was either a utility template message or non-template message sent within a `customer service window <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#customer-service-windows>`_.
        FREE_ENTRY_POINT: Indicates the message is free because it is part of a `free-entry point conversation <https://developers.facebook.com/docs/whatsapp/pricing#free-entry-point-conversations>`_.
    """

    _check_value = str.islower
    _modify_value = str.lower

    REGULAR = "regular"
    FREE_CUSTOMER_SERVICE = "free_customer_service"
    FREE_ENTRY_POINT = "free_entry_point"

    UNKNOWN = "UNKNOWN"


class PricingCategory(utils.StrEnum):
    """
    Pricing category.

    Attributes:
        AUTHENTICATION: Indicates authentication rate applied.
        AUTHENTICATION_INTERNATIONAL: Indicates authentication-international rate applied.
        MARKETING: Indicates marketing rate applied.
        MARKETING_LITE: Indicates a `Marketing Messages Lite API <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/>`_ pricing applied.
        UTILITY: Indicates utility rate applied.
        SERVICE: Indicates service rate applied.
        REFERRAL_CONVERSION: Indicates a `free entry point conversation <https://developers.facebook.com/docs/whatsapp/pricing#free-entry-point-conversations>`_.
    """

    _check_value = str.islower
    _modify_value = str.lower

    AUTHENTICATION = "authentication"
    AUTHENTICATION_INTERNATIONAL = "authentication_international"
    MARKETING = "marketing"
    MARKETING_LITE = "marketing_lite"
    UTILITY = "utility"
    SERVICE = "service"
    REFERRAL_CONVERSION = "referral_conversion"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True)
class Pricing:
    """
    Represents the pricing of a message.

    - `'Pricing' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/pricing>`_.

    Attributes:
        billable: Indicates if the message is billable.
        model: The pricing model used for the message.
        type: The pricing type of the message (Only available from webhook v24.0^).
        category: The pricing category of the message.

    """

    billable: bool
    model: PricingModel
    type: PricingType | None
    category: PricingCategory

    @classmethod
    def from_dict(cls, data: dict):
        pricing_type = data.get("type") or data.get("pricing_type")
        return cls(
            billable=data.get("billable", data.get("type") == PricingType.REGULAR),
            model=PricingModel(data["pricing_model"]),
            type=PricingType(pricing_type) if pricing_type else None,
            category=PricingCategory(data["category"]),
        )
