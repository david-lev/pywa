from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from pywa.types.user import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.user import User as _User

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync
    from .calls import CallPermissions


class BaseUserAsync:
    _client: WhatsAppAsync
    preferred_id: str

    async def block(self) -> bool:
        """
        Block the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.block_users` with the user.

        Returns:
            bool: True if the user was blocked

        Raises:
            BlockUserError: If the user was not blocked
        """
        res = await self._client.block_users((self.preferred_id,))
        added = self.preferred_id in {u.preferred_id for u in res.added_users}
        if not added:
            raise res.errors
        return added

    async def unblock(self) -> bool:
        """
        Unblock the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.unblock_users` with the user.

        Returns:
            bool: True if the user was unblocked, False otherwise.
        """
        return self.preferred_id in {
            u.preferred_id
            for u in (
                await self._client.unblock_users((self.preferred_id,))
            ).removed_users
        }

    async def get_call_permissions(self) -> CallPermissions:
        """
        Get the call permissions of the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.get_call_permissions` with the user.

        Returns:
            CallPermissions: The call permissions of the user.
        """
        return await self._client.get_call_permissions(from_user=self.preferred_id)


@dataclasses.dataclass(frozen=True, slots=True)
class User(BaseUserAsync, _User):
    """
    Represents a WhatsApp user.

    Attributes:
        bsuid: The WhatsApp user’s BSUID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids>`_ for more information.
        wa_id: The user's phone number in international format (without the '+' sign). Will be unavailable if the user enables the username feature. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#phone-numbers>`_ for more information.
        name: The name of the user.
        username: The username of the user.
        identity_key_hash: The identity key hash of the user (Only if identity key check is enabled on the phone number settings).
        parent_bsuid: The Parent business-scoped user ID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#parent-business-scoped-user-ids>`_ for more information.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)
