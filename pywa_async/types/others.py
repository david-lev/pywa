from __future__ import annotations

import asyncio
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

    async def get_call_permissions(self) -> CallPermissions:
        """
        Get the call permissions of the user.

        - Shortcut for :meth:`~pywa.client.WhatsApp.get_call_permissions` with the user wa_id.

        Returns:
            CallPermissions: The call permissions of the user.
        """
        return await self._client.get_call_permissions(wa_id=self.wa_id)


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

        >>> from pywa import WhatsApp, types
        >>> wa = WhatsApp(...)
        >>> res = wa.get_blocked_users(pagination=types.Pagination(limit=100))
        >>> for user in res:
        ...     print(user.name, user.wa_id)
        ...
        >>> if res.has_next:
        ...     next_res = res.next()
        ...
        >>> print(res.all())

    Methods:
        next: Get the next page of results. if there is no next page, it returns empty Result.
        previous: Get the previous page of results. if there is no previous page, it returns empty Result.
        all: Get all results from the current page, previous pages, and next pages.
        empty: Returns an empty Result instance.

    Properties:
        has_next: Check if there is a next page of results.
        has_previous: Check if there is a previous page of results.
        before: Cursor that points to the start of the page of data that has been returned.
        after: Cursor that points to the end of the page of data that has been returned.
    """

    _wa: WhatsAppAsync

    @property
    def empty(self) -> Result[_T]:
        """Returns an empty Result instance."""
        return Result(
            wa=self._wa,
            response={
                "data": [],
                "paging": {"next": self._next_url, "cursors": self._cursors},
            },
            item_factory=self._item_factory,
        )

    async def next(self) -> Result[_T]:
        """
        Get the next page of results. if there is no next page, it returns empty Result.

        - Check if there is a next page using the :attr:`~pywa.types.others.Result.has_next` property before calling this method.
        """
        if self.has_next:
            # noinspection PyProtectedMember
            response = await self._wa.api._make_request(
                method="GET", endpoint=self._next_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return self.empty

    async def previous(self) -> Result[_T]:
        """
        Get the previous page of results. if there is no previous page, it returns empty Result.

        - Check if there is a previous page using the :attr:`~pywa.types.others.Result.has_previous` property before calling this method.
        """
        if self.has_previous:
            # noinspection PyProtectedMember
            response = await self._wa.api._make_request(
                method="GET", endpoint=self._previous_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return self.empty

    async def all(
        self,
        *,
        sleep: float = 0.0,
    ) -> list[_T]:
        """
        Get all results from the current page, previous pages, and next pages.

        - Make sure to provide higher limit in the ``Pagination`` parameter to avoid hitting rate limits.
        - Also consider using the ``sleep`` parameter to avoid hitting rate limits.

        Args:
            sleep: The number of seconds to sleep between requests to avoid hitting rate limits. Default is 0.0 (no sleep).

        Returns:
            A list of all results from the current page, previous pages, and next pages.
        """
        before_data = []
        after_data = []

        prev = self
        while prev.has_previous:
            if sleep > 0:
                await asyncio.sleep(sleep)
            prev = await prev.previous()
            # noinspection PyProtectedMember
            before_data = prev._data + before_data

        next_page = self
        while next_page.has_next:
            if sleep > 0:
                await asyncio.sleep(sleep)
            next_page = await next_page.next()
            after_data += next_page._data

        return before_data + self._data + after_data
