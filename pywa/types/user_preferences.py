"""This module contains updates related to user preferences in WhatsApp."""

from __future__ import annotations

__all__ = [
    "UserPreferences",
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
class UserPreferences(BaseUserUpdate):
    """
    Represents user preferences updates from WhatsApp.

    Attributes:
        id: The ID of the update (not a real ID, just a hash of the update).
        metadata: The metadata of the message (to which phone number it was sent).
        timestamp: The timestamp when the update was sent.
        from_user: The user who makes the preference change.
        value: The value of the user preference.
        detail: A description of the user preference.
        category: The category of the user preference.
    """

    value: str
    detail: str
    category: UserPreferenceCategory

    @staticmethod
    def _get_cls_kwargs(client: WhatsApp, update: dict) -> dict:
        """Extracts the relevant fields from the update."""
        preferences = (value := update["entry"][0]["changes"][0]["value"])[
            "user_preferences"
        ][0]
        return {
            "_client": client,
            "raw": update,
            "id": str(hash(str(update))),  # not a real ID, just a hash of the update
            "metadata": Metadata.from_dict(value["metadata"]),
            "timestamp": datetime.datetime.fromtimestamp(
                int(preferences["timestamp"]),
                datetime.timezone.utc,
            ),
            "from_user": client._usr_cls.from_dict(value["contacts"][0], client=client),
            "value": preferences["value"],
            "detail": preferences["detail"],
            "category": UserPreferenceCategory(preferences["category"]),
        }

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> UserPreferences:
        return cls(**cls._get_cls_kwargs(client, update))


class UserPreferenceCategory(utils.StrEnum):
    """
    The category of the user preference.

    Attributes:
        MARKETING_MESSAGES: User preferences for marketing messages.
    """

    MARKETING_MESSAGES = "marketing_messages"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: str) -> str:
        _logger.warning(
            "Unknown user preference category: %s. Defaulting to UNKNOWN.", value
        )
        return cls.UNKNOWN


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class UserMarketingPreferences(UserPreferences):
    """
    Represents user marketing preferences updates from WhatsApp.

    - `'User preferences for marketing messages' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates#user-preferences-for-marketing-messages>`_.

    Attributes:
        id: The ID of the update (not a real ID, just a hash of the update).
        metadata: The metadata of the message (to which phone number it was sent).
        timestamp: The timestamp when the update was sent.
        from_user: The user who made the marketing preference change.
        value: The marketing preference chosen by the user, either 'stop' or 'resume'.
        detail: A description of the marketing preference change (e.g., "User requested to stop marketing messages").
        category: The category of the user preference, which is always 'marketing_messages'.
    """

    value: MarketingPreference

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> UserMarketingPreferences:
        kwargs = cls._get_cls_kwargs(client, update)
        kwargs["value"] = MarketingPreference(kwargs["value"])
        return cls(**kwargs)


class MarketingPreference(utils.StrEnum):
    """
    The marketing preference chosen by the user.

    Attributes:
        STOP: The user has requested to stop receiving marketing messages.
        RESUME: The user has requested to resume receiving marketing messages.
    """

    STOP = "stop"
    RESUME = "resume"
