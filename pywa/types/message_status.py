"""This module contains the types related to message status updates."""

from __future__ import annotations

import warnings

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
import logging
import datetime
from typing import TYPE_CHECKING, Generic

from .. import utils
from ..errors import WhatsAppError

from .base_update import BaseUserUpdate  # noqa
from .others import Metadata, User

if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)


class MessageStatusType(utils.StrEnum):
    """
    Message status type.

    Attributes:
        SENT: The message was sent.
        DELIVERED: The message was delivered.
        READ: The message was read.
        FAILED: The message failed to send (you can access the ``.error`` attribute for more information).
    """

    _check_value = str.islower
    _modify_value = str.lower

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

    UNKNOWN = "UNKNOWN"


class ConversationCategory(utils.StrEnum):
    """
    Conversation category.

    Attributes:
        AUTHENTICATION: The conversation is related to authentication.
        MARKETING: The conversation is related to marketing.
        MARKETING_LITE: The conversation is related to marketing lite.
        UTILITY: The conversation is related to utility.
        SERVICE: The conversation is related to service.
        REFERRAL_CONVERSION: The conversation is related to referral conversion.
        UNKNOWN: The conversation category is unknown.
    """

    _check_value = str.islower
    _modify_value = str.lower

    AUTHENTICATION = "authentication"
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

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> MessageStatus:
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
                wa_id=status["recipient_id"], name=None, _client=client
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
        CBP: Indicates conversation-based pricing applies.
        PMP: Indicates per-message pricing applies.
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
        AUTHENTICATION: Indicates an authentication template message.
        AUTHENTICATION_INTERNATIONAL: Indicates an authentication template message sent to a WhatsApp user in a country or region that has authentication-international rates.
        MARKETING: Indicates a marketing template message.
        MARKETING_LITE: Indicates a marketing template message sent via MM Lite API.
        UTILITY: Indicates a utility template message.
        SERVICE: Indicates a non-template message.
        REFERRAL_CONVERSION: Indicates the message is part of a `free entry point conversation <https://developers.facebook.com/docs/whatsapp/pricing#free-entry-point-conversations>`_.
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
        return cls(
            billable=data.get("billable", data.get("type") == PricingType.REGULAR),
            model=PricingModel(data["pricing_model"]),
            type=PricingType(data["pricing_type"]) if "pricing_type" in data else None,
            category=PricingCategory(data["category"]),
        )
