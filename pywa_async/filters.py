from __future__ import annotations

from pywa.filters import *  # noqa MUST BE IMPORTED FIRST
from pywa.filters import (
    Filter as _Filter,
)  # noqa MUST BE IMPORTED FIRST

import abc
from typing import TYPE_CHECKING, Callable, TypeVar, Awaitable

from . import _helpers as helpers
from pywa.types.base_update import (
    BaseUpdate as _BaseUpdate,
)  # noqa


if TYPE_CHECKING:
    from pywa_async import WhatsApp as _Wa


_T = TypeVar("_T", bound=_BaseUpdate)


class Filter(_Filter):
    @abc.abstractmethod
    async def __call__(self, wa: _Wa, update: _T) -> bool: ...

    def __and__(self, other: Filter) -> Filter:
        return AndFilter(self, other)

    def __or__(self, other: Filter) -> Filter:
        return OrFilter(self, other)

    def __invert__(self) -> Filter:
        return NotFilter(self)


class AndFilter(Filter):
    def __init__(self, left: Filter, right: Filter):
        self.left = left
        self.right = right

    async def __call__(self, wa: _Wa, update: _T) -> bool:
        return await self.left(wa, update) and await self.right(wa, update)


class OrFilter(Filter):
    def __init__(self, left: Filter, right: Filter):
        self.left = left
        self.right = right

    async def __call__(self, wa: _Wa, update: _T) -> bool:
        return await self.left(wa, update) or self.right(wa, update)


class NotFilter(Filter):
    def __init__(self, fil: Filter):
        self.filter = fil

    async def __call__(self, wa: _Wa, update: _T) -> bool:
        return not self.filter(wa, update)


def new(
    func: Callable[[_Wa, _T], bool | Awaitable[bool]], name: str | None = None
) -> Filter:
    is_async = helpers.is_async_callable(func)

    async def _call(self, wa: _Wa, update: _T) -> bool:
        return await func(wa, update) if is_async else func(wa, update)

    return type(
        name or func.__name__ or "filter",
        (Filter,),
        {"__call__": _call},
    )()
