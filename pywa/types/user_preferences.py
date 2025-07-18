"""This module contains updates related to user preferences in WhatsApp."""

from __future__ import annotations

__all__ = [
    "UserMarketingPreferences",
    "UserPreferenceCategory",
    "MarketingPreference",
]

import dataclasses
import datetime
import logging
from typing import TYPE_CHECKING

from .. import utils

from .base_update import BaseUserUpdate  # noqa
from .others import Metadata

if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class UserMarketingPreferences(BaseUserUpdate):
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
    """

    value: MarketingPreference
    detail: str
    category: UserPreferenceCategory

    _webhook_field = "user_preferences"

    @property
    def message_id_to_reply(self) -> str:
        """Raises an error because user preferences updates cannot be replied."""
        raise ValueError(
            "You cannot use `message_id_to_reply` to quote a user preference update."
        )

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> UserMarketingPreferences:
        prefs = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "user_preferences"
        ][0]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=entry["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            timestamp=datetime.datetime.fromtimestamp(
                int(prefs["timestamp"]),
                datetime.timezone.utc,
            ),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            value=MarketingPreference(prefs["value"]),
            detail=prefs["detail"],
            category=UserPreferenceCategory(prefs["category"]),
        )

    def __bool__(self):
        """Returns True if the user has not requested to stop receiving marketing messages."""
        return self.value != MarketingPreference.STOP


class MarketingPreference(utils.StrEnum):
    """
    The marketing preference chosen by the user.

    Attributes:
        STOP: The user has requested to stop receiving marketing messages.
        RESUME: The user has requested to resume receiving marketing messages.
    """

    _check_value = str.islower
    _modify_value = str.lower

    STOP = "stop"
    RESUME = "resume"

    UNKNOWN = "UNKNOWN"


class UserPreferenceCategory(utils.StrEnum):
    """
    The category of the user preference.

    Attributes:
        MARKETING_MESSAGES: User preferences for marketing messages.
    """

    _check_value = str.islower
    _modify_value = str.lower

    MARKETING_MESSAGES = "marketing_messages"

    UNKNOWN = "UNKNOWN"
