from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .calls import CallPermissions


@dataclasses.dataclass(frozen=True, slots=True)
class User:
    """
    Represents a WhatsApp user.

    Attributes:
        bsuid: The WhatsApp user’s BSUID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids>`_ for more information.
        wa_id: The user's phone number in international format (without the '+' sign). Will be unavailable if the user enables the username feature. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#phone-numbers>`_ for more information.
        name: The name of the user.
        username: The username of the user.
        identity_key_hash: The identity key hash of the user (Only if identity key check is enabled on the phone number settings).
        parent_id: The Parent business-scoped user ID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#parent-business-scoped-user-ids>`_ for more information.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    bsuid: str
    name: str
    wa_id: str | None
    username: str | None
    identity_key_hash: str | None
    parent_id: str | None

    @property
    def preferred_id(self) -> str:
        """
        Returns the preferred identifier (``wa_id`` or ``bsuid``) for this user.

        The identifier is selected according to the client's
        ``user_identifier_priority`` configuration. For example, if the priority is
        ``(WA_ID, BSUID)``, this will return ``wa_id`` if available, otherwise
        ``bsuid``.

        This property is used internally by pywa when performing user-related
        actions such as replying to messages or blocking users, to determine which identifier to use.

        Note:
            This value is context-dependent and may change based on client
            configuration. For deterministic behavior, use ``wa_id`` or
            ``bsuid`` directly.
        """
        for identifier in self._client._user_identifier_priority:
            value = getattr(self, identifier.user_attr, None)
            if value is not None:
                return value
        raise ValueError(
            f"User {self} does not have any identifier available based on the client's identifier priority configuration."
        )

    @classmethod
    def from_contact(cls, data: dict, client: WhatsApp) -> User:
        return cls(
            _client=client,
            bsuid=data["user_id"],
            wa_id=data.get("wa_id") or None,  # avoid empty string
            name=data["profile"]["name"],
            username=data["profile"].get("username"),
            parent_id=data.get("parent_user_id"),
            identity_key_hash=data.get("identity_key_hash"),
        )

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> User:
        return cls(
            _client=client,
            bsuid=data.get("user_id"),
            wa_id=data.get("wa_id"),
            name=None,
            username=None,
            parent_id=None,
            identity_key_hash=None,
        )

    @classmethod
    def from_sent_update(
        cls, data: dict, identity_key_hash: str | None, client: WhatsApp
    ) -> User:
        return cls(
            _client=client,
            bsuid=data.get("user_id"),
            wa_id=data.get("wa_id"),
            name=None,
            username=None,
            parent_id=None,
            identity_key_hash=identity_key_hash,
        )

    def block(self) -> bool:
        """
        Block the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.block_users` with the user wa_id.

        Returns:
            bool: True if the user was blocked

        Raises:
            BlockUserError: If the user was not blocked
        """
        res = self._client.block_users((self.wa_id,))
        added = self.wa_id in {u.wa_id for u in res.added_users}
        if not added:
            raise res.errors
        return added

    def unblock(self) -> bool:
        """
        Unblock the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.unblock_users` with the user wa_id.

        Returns:
            bool: True if the user was unblocked, False otherwise.
        """
        return self.wa_id in {
            u.wa_id for u in self._client.unblock_users((self.wa_id,)).removed_users
        }

    def get_call_permissions(self) -> CallPermissions:
        """
        Get the call permissions of the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.get_call_permissions` with the user wa_id.

        Returns:
            CallPermissions: The call permissions of the user.
        """
        return self._client.get_call_permissions(wa_id=self.wa_id)

    def as_vcard(self) -> str:
        """Get the user as a vCard."""
        return "\n".join(
            (
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{self.name}",
                f"TEL;type=CELL;type=VOICE:+{self.wa_id}",
                "END:VCARD",
            )
        )
