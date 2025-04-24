from __future__ import annotations

from pywa.types.others import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.others import Result as _Result, _T


class Result(_Result):
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
