"""This module contains updates related to user preferences in WhatsApp."""

from __future__ import annotations

__all__ = [
    "MarketingPreference",
    "UserMarketingPreferences",
    "UserPreferenceCategory",
]

from pywa.types.user_preferences import *
from pywa.types.user_preferences import (
    UserMarketingPreferences as _UserMarketingPreferences,
)

from .base_update import BaseUserUpdateAsync


class UserMarketingPreferences(BaseUserUpdateAsync, _UserMarketingPreferences):
    """
    Represents user marketing preferences updates from WhatsApp.

    - `'User preferences for marketing messages' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates#user-preferences-for-marketing-messages>`_.

    Attributes:
        id: The WhatsApp Business Account ID that the update was sent to.
        metadata: The metadata of the message (to which phone number it was sent).
        timestamp: The timestamp when the update was sent.
        from_user: The user who made the marketing preference change.
        value: The marketing preference chosen by the user, either ``stop`` or ``resume``.
        detail: A description of the marketing preference change (e.g. `User requested to stop marketing messages`).
        category: The category of the user preference, which is always ``marketing_messages``.
        signup_id: The signup id the user click on.
    """
