from __future__ import annotations

"""This module contains the types related to system messages."""

__all__ = ["PhoneNumberChange", "IdentityChange", "SystemType", "Identity"]


from .. import utils

import dataclasses
import datetime
from typing import TYPE_CHECKING

from .base_update import BaseUserUpdate  # noqa
from .others import (
    MessageType,
    Metadata,
)

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class PhoneNumberChange(BaseUserUpdate):
    """
    A update received when a user changes their phone number on WhatsApp.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The type of the message (always ``MessageType.SYSTEM``).
        from_user: The user who changed their phone number.
        timestamp: The timestamp when the message was arrived to WhatsApp servers (in UTC).
        old_wa_id: The old WhatsApp ID of the user.
        new_wa_id: The new WhatsApp ID of the user.
        body: The body of the system message (e.g., `John changed their phone number`).
    """

    type: MessageType
    sys_type: SystemType
    old_wa_id: str
    new_wa_id: str
    body: str

    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> PhoneNumberChange:
        sys = (
            msg := (value := (entry := update["entry"][0])["changes"][0]["value"])[
                "messages"
            ][0]
        )["system"]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            metadata=Metadata.from_dict(value["metadata"]),
            type=MessageType(msg["type"]),
            sys_type=SystemType(sys["type"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            old_wa_id=sys["customer"],
            new_wa_id=sys.get("new_wa_id", sys["wa_id"]),  # v12^ wa_id
            body=sys["body"],
        )


class SystemType(utils.StrEnum):
    """
    The type of the system message.

    Attributes:
        CUSTOMER_CHANGED_NUMBER: A customer changed their phone number.
        CUSTOMER_IDENTITY_CHANGED: A customer changed their profile information.
    """

    CUSTOMER_CHANGED_NUMBER = "customer_changed_number"
    CUSTOMER_IDENTITY_CHANGED = "customer_identity_changed"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class IdentityChange(BaseUserUpdate):
    """
    A message received when a user changes their profile information on WhatsApp.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The type of the message (always ``MessageType.SYSTEM``).
        from_user: The user who changed their profile information.
        timestamp: The timestamp when the message was arrived to WhatsApp servers (in UTC).
        body: The body of the system message (e.g., `John changed their profile information`).
        identity: The new identity of the user (see :class:`Identity`).
    """

    type: MessageType
    sys_type: SystemType
    body: str
    identity: Identity

    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> IdentityChange:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "messages"
        ][0]
        sys, identity = msg["system"], msg["identity"]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            type=MessageType(msg["type"]),
            sys_type=SystemType(sys["type"]),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            body=sys["body"],
            identity=Identity.from_dict(identity),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Identity:
    """
    Represents a user's identity on WhatsApp.

    Attributes:
        acknowledged: State of acknowledgment.
        created_timestamp: The time when the WhatsApp Business Management API detected the customer may have changed their profile information.
        hash: The hash of the identity.
    """

    acknowledged: bool
    created_timestamp: datetime.datetime
    hash: str

    @classmethod
    def from_dict(cls, data: dict) -> Identity:
        return cls(
            acknowledged=data["acknowledged"],
            created_timestamp=datetime.datetime.fromtimestamp(
                int(data["created_timestamp"]), datetime.timezone.utc
            ),
            hash=data["hash"],
        )
