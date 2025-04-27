from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Optional

__all__ = ["init", "get_logger", "set_level"]

_RICH_AVAILABLE: bool
try:
    from rich.logging import RichHandler  # type: ignore

    _RICH_AVAILABLE = True
except ModuleNotFoundError:
    _RICH_AVAILABLE = False

_COLORAMA_AVAILABLE: bool
try:
    import colorama  # type: ignore

    colorama.just_fix_windows_console()
except ModuleNotFoundError:
    _COLORAMA_AVAILABLE = False
else:
    _COLORAMA_AVAILABLE = True

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class _ColourFormatter(logging.Formatter):
    """ANSI colour formatter for when *rich* is not installed."""

    _COLOURS = {
        "DEBUG": "\033[36m",  # cyan
        "INFO": "\033[32m",  # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",  # red
        "CRITICAL": "\033[41m",  # red background
    }

    _EMOJIS = {
        "DEBUG": "🐞",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "🛑",
        "CRITICAL": "🔥",
    }

    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        level_colour = self._COLOURS.get(record.levelname, "")
        emoji = self._EMOJIS.get(record.levelname, "")
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{ts} {level_colour}{record.levelname:<8}{self._RESET} {emoji} {record.getMessage()}"
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return msg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
_DEFAULT_LEVEL = logging.INFO
_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_DIR = "logs"
_FILE_NAME = "app.log"

_root_initialised = False


def init(
    *,
    level: int = _DEFAULT_LEVEL,
    log_dir: str | os.PathLike[str] = _LOG_DIR,
    file_name: str = _FILE_NAME,
    json_file: bool = False,
    capture_warnings: bool = True,
) -> None:
    """Initialise root logger exactly once."""

    global _root_initialised
    if _root_initialised:
        return

    os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if _RICH_AVAILABLE:
        # Add emoji to messages by using markup and prepending emoji to the message
        class EmojiRichHandler(RichHandler):
            _EMOJIS = {
                "DEBUG": "🐞",
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "🛑",
                "CRITICAL": "🔥",
            }
            def emit(self, record):
                emoji = self._EMOJIS.get(record.levelname, "")
                if emoji and isinstance(record.msg, str):
                    record.msg = f"{emoji} {record.msg}"
                super().emit(record)
        console_handler: logging.Handler = EmojiRichHandler(rich_tracebacks=True, show_level=False, markup=True)
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(_ColourFormatter())
    root.addHandler(console_handler)

    file_path = os.path.join(log_dir, file_name)
    file_handler = TimedRotatingFileHandler(file_path, when="midnight", encoding="utf-8")
    if json_file:
        file_handler.setFormatter(_JsonFormatter())
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s » %(message)s", _DEFAULT_FORMAT)
        file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    def _excepthook(exc_type, exc_value, exc_tb):
        root.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    if capture_warnings:
        logging.captureWarnings(True)

    _root_initialised = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger initialised via :pyfunc:`init` if not already."""

    if not _root_initialised:
        init()
    return logging.getLogger(name)


def set_level(level: int | str) -> None:
    """Dynamically raise/lower root logger level."""

    root = logging.getLogger()
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
    root.setLevel(level)
    for handler in root.handlers:
        handler.setLevel(level)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="plog quick demo")
    parser.add_argument("--debug", action="store_true", help="run with DEBUG level")
    args = parser.parse_args()

    init(level=logging.DEBUG if args.debug else logging.INFO)
    log = get_logger(__name__)

    log.debug("debug message")
    log.info("info message")
    log.warning("warning message")
    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("oh no – cannot divide by zero")
