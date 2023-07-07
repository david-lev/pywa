from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from pywa.errors import WhatsAppError
from .others import _StrEnum
from .base_update import BaseUpdate

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .base_update import BaseUpdate
    from .others import Metadata, MessageType, User


class MessageStatusType(_StrEnum):
    """Message status type."""
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'
    UNKNOWN = 'unknown'

    def __missing__(self, key):
        return self.UNKNOWN


@dataclass(frozen=True, slots=True)
class MessageStatus(BaseUpdate):
    """
    Represents the status of a message.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#statuses-object

    Attributes:
        id: The ID of the message that the status is for.
        metadata: The metadata of the message (to which phone number it was sent).
        status: The status of the message.
        timestamp: The timestamp when the status was updated.
        from_user: The user who the message was sent to.
        error: The error that occurred (if status is ``failed``).
    """
    status: MessageStatusType
    error: WhatsAppError | None

    @classmethod
    def from_dict(cls, client: WhatsApp, value: dict):
        status = value['statuses'][0]
        status_type = MessageStatusType(status['status'])
        return cls(
            _client=client,
            id=status['id'],
            metadata=Metadata.from_dict(**value['metadata']),
            type=MessageType.MESSAGE_STATUS,
            status=status_type,
            timestamp=datetime.fromtimestamp(int(status['timestamp'])),
            from_user=User(wa_id=status['recipient_id'], name=None),
            error=WhatsAppError.from_incoming_error(status['errors'][0])
            if status_type == MessageStatusType.FAILED else None
        )
