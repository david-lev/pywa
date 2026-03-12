from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from pywa.types import User as _User

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync
    from .calls import CallPermissions


@dataclasses.dataclass(frozen=True, slots=True)
class User(_User):
    """
    Represents a WhatsApp user.

    Attributes:
        wa_id: The WhatsApp ID of the user (The phone number with the country code).
        name: The name of the user (``None`` on :class:`MessageStatus`).
        identity_key_hash: The identity key hash of the user (Only if identity key check is enabled on the phone number settings).
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def block(self) -> bool:
        """
        Block the user.

        - Shortcut for :meth:`~pywa_async.client.WhatsApp.block_users` with the user wa_id.

        Returns:
            bool: True if the user was blocked

        Raises:
            BlockUserError: If the user was not blocked
        """
        res = await self._client.block_users((self.wa_id,))
        added = self.wa_id in {u.wa_id for u in res.added_users}
        if not added:
            raise res.errors
        return added

    async def unblock(self) -> bool:
        """
        Unblock the user.

        - Shortcut for :meth:`~pywa_async.client.WhatsApp.unblock_users` with the user wa_id.

        Returns:
            bool: True if the user was unblocked, False otherwise.
        """
        return self.wa_id in {
            u.wa_id
            for u in (await self._client.unblock_users((self.wa_id,))).removed_users
        }

    async def get_call_permissions(self) -> CallPermissions:
        """
        Get the call permissions of the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.get_call_permissions` with the user wa_id.

        Returns:
            CallPermissions: The call permissions of the user.
        """
        return await self._client.get_call_permissions(wa_id=self.wa_id)
