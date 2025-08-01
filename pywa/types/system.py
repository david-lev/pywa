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
        sys_type: The type of the system message (always ``SystemType.USER_CHANGED_NUMBER``).
        from_user: The user who changed their phone number. THIS IS THE OLD WA ID!
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
            from_user=client._usr_cls(_client=client, wa_id=msg["from"], name=None),
            old_wa_id=sys.get("customer", msg["from"]),  # v12^ from
            new_wa_id=sys.get("new_wa_id", sys["wa_id"]),  # v12^ wa_id
            body=sys["body"],
        )


class SystemType(utils.StrEnum):
    """
    The type of the system message.

    Attributes:
        USER_CHANGED_NUMBER: A user changed their phone number.
        CUSTOMER_IDENTITY_CHANGED: A user changed their profile information.
    """

    USER_CHANGED_NUMBER = "user_changed_number"
    CUSTOMER_IDENTITY_CHANGED = "customer_identity_changed"

    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: str):
        # the documentation very confusing about the values of system types
        if (
            value == "customer_changed_number"
        ):  # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components#messages-object
            return cls.USER_CHANGED_NUMBER  # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#user-changed-number-notification
        return super()._missing_(value)


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
