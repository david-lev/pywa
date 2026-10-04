"""Internal logging infrastructure shared by the sync and async ``Server``/CLI implementations."""

from __future__ import annotations

import dataclasses
import datetime
import enum
import hashlib
import logging
import os
import sys
import time
import warnings
from typing import TYPE_CHECKING, TextIO, cast

from .errors import ThrottlingError

if TYPE_CHECKING:
    import httpx

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
    if endpoint and endpoint != "/":
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


def describe_raw_update(raw: dict) -> str:
    """Short, PII-free description of a raw webhook payload; never raises on odd shapes."""
    try:
        change = raw["entry"][0]["changes"][0]
        return f"field={change['field']} waba={raw['entry'][0]['id']}"
    except (KeyError, IndexError, TypeError):
        return "field=<unknown>"


def describe_update(update: object) -> str:
    """
    A PII-free one-liner for a constructed update, e.g. ``Message(text) wamid.…a1b2c3d4``.

    Only the class name, the update's own ``_log_label`` (an enum value, if any) and the
    tail of the message id are used - never user names, phone numbers or message content.
    """
    name = type(update).__name__
    label = getattr(update, "_log_label", None)
    if label:
        name = f"{name}({label})"
    ident = getattr(update, "id", None)
    if isinstance(ident, str) and ident.startswith("wamid."):
        # the start of a real `wamid` is base64 of the user's phone number or BSUID: keep only the tail
        body = ident.removeprefix("wamid.")
        return f"{name} wamid.{body if len(body) <= 8 else '…' + body[-8:]}"
    return name


def _is_empty(value: object) -> bool:
    return value is None or value in ("", b"", (), [], {})


def compact_repr(obj: object) -> str:
    """
    ``repr`` that drops ``None``/empty fields (``False`` is kept: it is a real value), so a
    dataclass with 30 optional fields prints only what is actually set.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        parts = [
            f"{f.name}={compact_repr(value)}"
            for f in dataclasses.fields(obj)
            if f.repr and not _is_empty(value := getattr(obj, f.name, None))
        ]
        return f"{type(obj).__name__}({', '.join(parts)})"
    if isinstance(obj, (list, tuple)):
        inner = ", ".join(compact_repr(v) for v in obj)
        return f"[{inner}]" if isinstance(obj, list) else f"({inner})"
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return repr(obj)


def _truncate(text: str, limit: int) -> str:
    return (
        text if len(text) <= limit else f"{text[:limit]}...(+{len(text) - limit} chars)"
    )


def describe_request(method: str, endpoint: str) -> str:
    """``"POST /123/messages"``, with any query string dropped (it may hold tokens)."""
    return f"{method.upper()} {str(endpoint).split('?', 1)[0]}"


def describe_request_kwargs(kwargs: dict, *, limit: int = 1000) -> str:
    """Compact, truncated view of the ``httpx`` request kwargs (uploads shown as ``<files>``)."""
    shown = {
        k: "<files>" if k == "files" else v
        for k, v in kwargs.items()
        if v not in (None, {}, [])
    }
    return _truncate(str(shown), limit)


def _is_throttling_code(code: object) -> bool:
    return any(
        code in getattr(cls, "__error_codes__", ())
        for cls in ThrottlingError.__subclasses__()
    )


def log_api_response(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    response: httpx.Response,
    started: float,
) -> None:
    """
    Log the outcome of a Graph API call: DEBUG for success, WARNING for an API error
    (with its code/message, but never the body), full body at DEBUG/TRACE.
    """
    elapsed = (time.perf_counter() - started) * 1000
    status = response.status_code
    if status < 400:
        if not logger.isEnabledFor(logging.DEBUG):
            return
        what = describe_request(method, endpoint)
        logger.debug("%s -> %d (%.0fms)", what, status, elapsed)
    else:
        what = describe_request(method, endpoint)
        err_code = None
        try:
            err = response.json()["error"]
            err_code = err.get("code")
            detail = f"code={err.get('code')} {err.get('message')!r}"
            trace_id = err.get("fbtrace_id")
            if trace_id:
                detail += f" fbtrace_id={trace_id}"
        except (ValueError, KeyError, TypeError, AttributeError):
            detail = "non-standard error body"
        if status == 429 or _is_throttling_code(err_code):
            detail += " [rate limit hit: slow down and retry later]"
        logger.warning("%s -> %d (%.0fms) %s", what, status, elapsed, detail)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s response: %s", what, _truncate(response.text, 500))
    if logger.isEnabledFor(TRACE):
        logger.log(TRACE, "%s full response: %s", what, response.text)


def format_banner(lines: list[str]) -> str:
    """Box a list of lines into the startup banner shared by the CLI and ``Server.run``."""
    width = 40
    return "\n".join([lines[0], "-" * width, *lines[1:], "-" * width])


def emit_banner(lines: list[str], *, stream: TextIO | None = None) -> None:
    """
    Print the startup banner plainly to stderr (no timestamp/level/logger prefix): it is
    UI, not a log event, and it should show regardless of the configured log level.
    """
    stream = stream or sys.stderr
    stream.write(f"\n{format_banner(lines)}\n\n")
    stream.flush()


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


_LEVEL_ATTR = "_pywa_configured_level"
_original_showwarning = warnings.showwarning


def _log_warning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: TextIO | None = None,
    line: str | None = None,
) -> None:
    """
    ``warnings.showwarning`` replacement that logs ``Category: message (file.py:42)``
    instead of the default ``path:42: Category: message`` + echoed source line.
    """
    if file is not None:
        _original_showwarning(message, category, filename, lineno, file, line)
        return
    logging.getLogger("py.warnings").warning(
        "%s: %s (%s:%d)", category.__name__, message, os.path.basename(filename), lineno
    )


def setup_console_logging(
    level: str | int = "info", *, stream: TextIO | None = None
) -> None:
    """
    Configure console logging for the processes that own the application (``Server.run``,
    the ``pywa`` CLI and the ASGI factory uvicorn calls in each worker).

    Note:
        - This also routes ``warnings.warn`` calls (from pywa and other libraries)
          through the logging handler, as ``Category: message (file.py:42)``, instead
          of printing them directly to stderr.
        - If the root logger already has handlers (the host application configured
          logging itself), no handler is added - only the levels are applied - so
          every record isn't printed twice and the host's format is respected.
    """
    resolved = resolve_log_level(level)
    stream = stream or sys.stderr

    warnings.showwarning = _log_warning  # ty: ignore[invalid-assignment]

    root = logging.getLogger()
    handler = next(
        (h for h in root.handlers if getattr(h, _CONSOLE_HANDLER_ATTR, False)),
        None,
    )
    if handler is not None:
        handler.setFormatter(ColorFormatter(use_color=_color_enabled(stream)))
    elif not root.handlers:
        handler = logging.StreamHandler(stream)
        setattr(handler, _CONSOLE_HANDLER_ATTR, True)
        handler.setFormatter(ColorFormatter(use_color=_color_enabled(stream)))
        root.addHandler(handler)

    pywa_logger = logging.getLogger("pywa")
    previous_level = getattr(pywa_logger, _LEVEL_ATTR, None)
    setattr(pywa_logger, _LEVEL_ATTR, resolved)
    pywa_logger.setLevel(resolved)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    if logging.DEBUG >= resolved != previous_level:
        pywa_logger.warning(
            "Log level is set to %s: logs may include your users' personal data (phone numbers, "
            "names, message content). Don't use it in production or ship these logs elsewhere unredacted.",
            logging.getLevelName(resolved),
        )
