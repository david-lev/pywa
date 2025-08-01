from __future__ import annotations

"""This module contains the types related to system messages."""

__all__ = ["PhoneNumberChange", "IdentityChange", "SystemType", "Identity"]

import dataclasses

from pywa.types.system import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.system import (
    PhoneNumberChange as _UserChangedNumber,
    IdentityChange as _UserIdentityChanged,
)
from .base_update import BaseUserUpdateAsync  # noqa


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class PhoneNumberChange(BaseUserUpdateAsync, _UserChangedNumber):
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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class IdentityChange(BaseUserUpdateAsync, _UserIdentityChanged):
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
