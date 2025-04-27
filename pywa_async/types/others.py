from __future__ import annotations

from typing import TYPE_CHECKING

from pywa.types.others import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.others import (
    Result as _Result,
    User as _User,
    UsersBlockedResult as _UsersBlockedResult,
    UsersUnblockedResult as _UsersUnblockedResult,
    _T,
)

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync


@dataclasses.dataclass(frozen=True, slots=True)
class User(_User):
    """
    Represents a WhatsApp user.

    Attributes:
        wa_id: The WhatsApp ID of the user (The phone number with the country code).
        name: The name of the user (``None`` on :class:`MessageStatus` or when message type is :class:`MessageType.SYSTEM`).
        input: The input of the recipient is only available when sending a message.
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
        added = self.wa_id in {u.input for u in res.added_users}
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
            u.input
            for u in (await self._client.unblock_users((self.wa_id,))).removed_users
        }


@dataclasses.dataclass(slots=True, frozen=True)
class UsersBlockedResult(_UsersBlockedResult):
    """
    Represents the result of blocking users operation.

    Attributes:
        added_users: The users that were successfully blocked.
        failed_users: The users that failed to be blocked. You can access the .errors attribute in each failure to get the error details.
        errors: The errors that occurred during the operation (if any).
    """

    added_users: tuple[User, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class UsersUnblockedResult(_UsersUnblockedResult):
    """
    Represents the result of unblocking users operation.

    Attributes:
        removed_users: The users that were successfully unblocked.
    """

    removed_users: tuple[User, ...]


class Result(_Result[_T]):
    """
    This class is used to handle paginated results from the WhatsApp API. You can iterate over the results, and also access the next and previous pages of results.

    - When using the ``next()`` or ``previous()`` methods, the results are returned as a new instance of the :class:`Result` class.
    - You can access the cursors using the ``before`` and ``after`` properties and use them later in the :class:`Pagination` object.

    Example:

        >>> from pywa_async import WhatsApp, types
        >>> wa = WhatsApp(...)
        >>> all_blocked_users = []
        >>> res = await wa.get_blocked_users(pagination=types.Pagination(limit=100))
        >>> while True:
        ...     all_blocked_users.extend(res)
        ...     if not res.has_next:
        ...         break
        ...     res = await res.next()
        >>> all_blocked_users
        [User(...), User(...), User(...), ...]
    """

    _wa: WhatsAppAsync

    async def next(self) -> Result[_T] | None:
        """Get the next page of results."""
        if self.has_next:
            # noinspection PyProtectedMember
            response = await self._wa.api._make_request(
                method="GET", endpoint=self._next_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return None

    async def previous(self) -> Result[_T] | None:
        """Get the previous page of results."""
        if self.has_previous:
            # noinspection PyProtectedMember
            response = await self._wa.api._make_request(
                method="GET", endpoint=self._previous_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return None
