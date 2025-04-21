from typing import TypeAlias, Iterable, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    from pywa.types.flows import NavigationItem, DataSource, Ref, MathExpression

__SingleScreenDataValType: TypeAlias = (
    str | int | float | bool | dict | datetime.date | DataSource
)

_ScreenDataValType: TypeAlias = (
    __SingleScreenDataValType | Iterable[__SingleScreenDataValType | NavigationItem]
)

_ScreenDataValTypeVar = TypeVar(
    "_ScreenDataValTypeVar",
    bound=_ScreenDataValType,
)

_FlowResponseDataType: TypeAlias = dict[
    str,
    str
    | int
    | float
    | bool
    | dict
    | DataSource
    | Iterable[str | int | float | bool | dict | DataSource | NavigationItem],
]

_MathT: TypeAlias = Ref | MathExpression | int | float

_RefT = TypeVar("_RefT", bound=Ref)
