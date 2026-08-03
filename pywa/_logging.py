"""Internal logging infrastructure shared by the sync and async ``Server``/CLI implementations."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import warnings
from typing import TextIO, cast

from .errors import PywaWarning

TRACE = 5
logging.addLevelName(TRACE, "TRACE")

ENV_LOG_LEVEL = "PYWA_LOG_LEVEL"
"""
Environment variable used to pass the resolved log level across a process boundary
- e.g. to a uvicorn ``--reload``/multi-worker subprocess that re-imports the app fresh
and would otherwise never see the level chosen in the parent process.
"""

_LEVEL_NAMES: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "trace": TRACE,
}

_LEVEL_COLORS: dict[int, str] = {
    TRACE: "\x1b[2;37m",  # dim white
    logging.DEBUG: "\x1b[36m",  # cyan
    logging.INFO: "\x1b[32m",  # green
    logging.WARNING: "\x1b[33m",  # yellow
    logging.ERROR: "\x1b[31m",  # red
    logging.CRITICAL: "\x1b[1;41m",  # bold on red
}
_CTX_COLOR = "\x1b[35m"  # magenta, for the [hash] [endpoint] prefix
_RESET = "\x1b[0m"
_DIM = "\x1b[2m"

_CONSOLE_HANDLER_ATTR = "_pywa_console_handler"
_CONSOLE_HANDLER_LEVEL_ATTR = "_pywa_console_handler_level"


def get_update_hash(update_bytes: bytes | bytearray) -> str:
    """Return a short, stable hash for an incoming raw webhook update body."""
    return hashlib.blake2s(update_bytes, digest_size=16).hexdigest()


def display_update_hash(update_hash: str) -> str:
    """Truncate a full update hash to a short, human-friendly form for logs."""
    return update_hash[:8]


def _context_prefix(update_hash: str | None, endpoint: str | None) -> str:
    """Build the ``"[hash] [endpoint] "`` text prefix, or ``""`` if there's no hash."""
    if not update_hash:
        return ""
    tag = f"[{display_update_hash(update_hash)}]"
    if endpoint:
        tag = f"{tag} [{endpoint}]"
    return f"{tag} "


class _UpdateLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        update_hash = cast("str | None", (self.extra or {}).get("update_hash"))
        endpoint = cast("str | None", (self.extra or {}).get("endpoint"))
        extra.setdefault("update_hash", update_hash)
        extra.setdefault("endpoint", endpoint)
        return f"{_context_prefix(update_hash, endpoint)}{msg}", kwargs


def bind_update_logger(
    logger: logging.Logger, update_hash: str | None, endpoint: str | None
) -> logging.LoggerAdapter:
    return _UpdateLoggerAdapter(
        logger, {"update_hash": update_hash, "endpoint": endpoint}
    )


def format_banner(lines: list[str]) -> str:
    """Box a list of lines into the startup banner shared by the CLI and ``Server.run``."""
    width = 40
    return "\n" + "\n".join([lines[0], "-" * width, *lines[1:], "-" * width])


def resolve_log_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    try:
        return _LEVEL_NAMES[level.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown log level: {level!r}. Expected one of {tuple(_LEVEL_NAMES)} or an int."
        ) from None


def _color_enabled(stream: TextIO) -> bool:
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


class ColorFormatter(logging.Formatter):
    """
    A ``logging.Formatter`` that colors output by level (when supported) and, when
    present, re-styles the ``[hash] [endpoint]`` context prefix baked into the message
    by :func:`bind_update_logger`.
    """

    def __init__(self, *, use_color: bool) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        time_str = self.formatTime(record, self.datefmt)
        level_str = f"{record.levelname:<8}"
        message = record.getMessage()

        if self.use_color:
            color = _LEVEL_COLORS.get(record.levelno, "")
            time_str = f"{_DIM}{time_str}{_RESET}"
            level_str = f"{color}{level_str}{_RESET}"
            prefix = _context_prefix(
                getattr(record, "update_hash", None), getattr(record, "endpoint", None)
            )
            if prefix and message.startswith(prefix):
                message = (
                    f"{_CTX_COLOR}{prefix.rstrip()}{_RESET} {message[len(prefix) :]}"
                )

        line = f"{time_str} {level_str} {record.name}: {message}"
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            line = f"{line}\n{record.exc_text}"
        if record.stack_info:
            line = f"{line}\n{self.formatStack(record.stack_info)}"
        return line


def setup_console_logging(
    level: str | int = "info", *, stream: TextIO | None = None
) -> None:
    """
    Note:
        This also enables ``logging.captureWarnings(True)`` process-wide, so
        ``warnings.warn`` calls (from pywa and other libraries) are routed through
        this handler instead of being printed directly to stderr.
    """
    resolved = resolve_log_level(level)
    stream = stream or sys.stderr

    logging.captureWarnings(True)

    root = logging.getLogger()
    handler = next(
        (h for h in root.handlers if getattr(h, _CONSOLE_HANDLER_ATTR, False)),
        None,
    )
    previous_level = getattr(handler, _CONSOLE_HANDLER_LEVEL_ATTR, None)
    if handler is None:
        handler = logging.StreamHandler(stream)
        setattr(handler, _CONSOLE_HANDLER_ATTR, True)
        root.addHandler(handler)
    setattr(handler, _CONSOLE_HANDLER_LEVEL_ATTR, resolved)
    handler.setFormatter(ColorFormatter(use_color=_color_enabled(stream)))

    logging.getLogger("pywa").setLevel(resolved)
    logging.getLogger("pywa.cli").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    if logging.DEBUG >= resolved != previous_level:
        warnings.warn(
            message=(
                f"Log level is set to {logging.getLevelName(resolved)}: this may include "
                "personal data from your users (phone numbers, names, message content) in "
                "the output. Avoid enabling this in production or sending these logs to a "
                "shared/third-party log aggregator without redacting them first."
            ),
            category=PywaWarning,
            stacklevel=2,
        )
