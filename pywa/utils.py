from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from importlib import import_module
from typing import Any, Callable, Protocol


def is_fastapi_app(app):
    """Check if the app is a FastAPI app."""
    try:
        return isinstance(app, import_module("fastapi").FastAPI)
    except ImportError:
        return False


def is_flask_app(app):
    """Check if the app is a Flask app."""
    try:
        return isinstance(app, import_module("flask").Flask)
    except ImportError:
        return False


class StrEnum(str, Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass(frozen=True, slots=True, kw_only=True)
class FromDict:
    """Allows to ignore extra fields when creating a dataclass from a dict."""

    # noinspection PyArgumentList
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        data.update(kwargs)
        return cls(
            **{k: v for k, v in data.items() if k in (f.name for f in fields(cls))}
        )


class FastAPI(Protocol):
    def get(self, path: str) -> Callable:
        ...

    def post(self, path: str) -> Callable:
        ...


class Flask(Protocol):
    def route(self, rule: str, **options: Any) -> Callable:
        ...
