from __future__ import annotations

from pywa.types.others import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.others import Result as _Result, _T


class Result(_Result):
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
