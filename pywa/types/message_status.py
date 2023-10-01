from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from pywa.errors import WhatsAppError
from pywa import utils
from .base_update import BaseUpdate
from .others import Metadata, User

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class MessageStatusType(utils.StrEnum):
    """
    Message status type.

    Attributes:
        SENT: The message was sent.
        DELIVERED: The message was delivered.
        READ: The message was read.
        FAILED: The message failed to send (you can access the error with ``.error`` attribute).
    """
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'

    @classmethod
    def _missing_(cls, value: str) -> MessageStatusType:
        return cls.FAILED


class ConversationCategory(utils.StrEnum):
    """
    Conversation category.

    Attributes:
        AUTHENTICATION: The conversation is related to authentication.
        MARKETING: The conversation is related to marketing.
        UTILITY: The conversation is related to utility.
        SERVICE: The conversation is related to service.
        REFERRAL_CONVERSION: The conversation is related to referral conversion.
        UNKNOWN: The conversation category is unknown.
    """
    AUTHENTICATION = 'authentication'
    MARKETING = 'marketing'
    UTILITY = 'utility'
    SERVICE = 'service'
    REFERRAL_CONVERSION = 'referral_conversion'
    UNKNOWN = 'unknown'

    @classmethod
    def _missing_(cls, value: str) -> ConversationCategory:
        return cls.UNKNOWN


@dataclass(frozen=True, slots=True, kw_only=True)
class MessageStatus(BaseUpdate):
    """
    Represents the status of a message.

    - `\`MessageStatus\` on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object>`_.

    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        from_user: The user who the message was sent to.
        conversation: The conversation the given status notification belongs to (Optional).
        pricing_model: Type of pricing model used by the business. Current supported value is CBP.
        error: The error that occurred (if status is ``failed``).
    """
    id: str
    metadata: Metadata
    from_user: User
    timestamp: datetime
    status: MessageStatusType
    conversation: Conversation | None
    pricing_model: str
    error: WhatsAppError | None

    @classmethod
    def from_dict(cls, client: WhatsApp, data: dict):
        status = data['statuses'][0]
        status_type = MessageStatusType(status['status'])
        return cls(
            _client=client,
            id=status['id'],
            metadata=Metadata.from_dict(data['metadata']),
            status=status_type,
            timestamp=datetime.fromtimestamp(int(status['timestamp'])),
            from_user=User(wa_id=status['recipient_id'], name=None),
            conversation=Conversation.from_dict(status['conversation']) if 'conversation' in status else None,
            pricing_model=status['pricing']['pricing_model'],
            error=WhatsAppError.from_incoming_error(status['errors'][0])
            if status_type == MessageStatusType.FAILED else None
        )


@dataclass(frozen=True, slots=True)
class Conversation:
    """
    Represents a conversation.

    - `\`Conversation\` on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/pricing#conversations>`_.

    Attributes:
        id: The ID of the conversation.
        category: The category of the conversation.
        expiration: The expiration date of the conversation (Optional, only for `sent` updates).

    """
    id: str
    category: ConversationCategory
    expiration: datetime | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data['id'],
            category=ConversationCategory(data['origin']['type']),
            expiration=datetime.fromtimestamp(int(data['expiration_timestamp']))
            if 'expiration_timestamp' in data else None
        )
