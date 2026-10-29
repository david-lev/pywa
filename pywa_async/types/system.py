"""This module contains the types related to system messages."""

from __future__ import annotations

__all__ = ["Identity", "IdentityChange", "PhoneNumberChange", "SystemType"]


from pywa.types.system import *
from pywa.types.system import (
    IdentityChange as _UserIdentityChanged,
)
from pywa.types.system import (
    PhoneNumberChange as _UserChangedNumber,
)

from .base_update import BaseUserUpdateAsync


class PhoneNumberChange(BaseUserUpdateAsync, _UserChangedNumber):
    """
    A update received when a user changes their phone number on WhatsApp.

    Attributes:
        id: The message ID.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The type of the message (always ``MessageType.SYSTEM``).
        sys_type: The type of the system message (``SystemType.USER_CHANGED_NUMBER`` or ``SystemType.USER_CHANGED_USER_ID``).
        from_user: The user who changed their phone number. The user will contain the old phone number in the ``wa_id`` field.
        timestamp: The timestamp when the message was arrived to WhatsApp servers (in UTC).
        old_wa_id: The old WhatsApp ID of the user (``None`` when the phone number is not shared).
        new_wa_id: The new WhatsApp ID of the user.
        old_user_id: The user's previous BSUID, if available.
        new_parent_id: he user’s new parent BSUID, if you have enabled parent BSUIDs
        old_parent_id: The user's previous parent BSUID, if you have enabled parent BSUIDs.
        body: The body of the system message (e.g., `John changed their phone number`).
    """


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
