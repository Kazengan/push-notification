from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from typing import Any, Optional


_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class LogType(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"


class Logger:
    """Simple stdout logger that mirrors the behaviour of the Node implementation."""

    _LEVEL_COLOURS = {
        LogLevel.DEBUG: "\x1b[36m",
        LogLevel.INFO: "\x1b[34m",
        LogLevel.WARN: "\x1b[33m",
        LogLevel.ERROR: "\x1b[31m",
    }

    @staticmethod
    def bind_request_id(request_id: Optional[str]) -> object:
        return _request_id.set(request_id)

    @staticmethod
    def reset_request_id(token: object) -> None:
        _request_id.reset(token)

    @staticmethod
    def info(message: Any, data: Any | None = None) -> None:
        Logger._log(LogLevel.INFO, message, data)

    @staticmethod
    def error(message: Any, data: Any | None = None) -> None:
        Logger._log(LogLevel.ERROR, message, data)

    @staticmethod
    def request(message: Any, data: Any | None = None) -> None:
        Logger._log(LogLevel.INFO, message, data, log_type=LogType.REQUEST)

    @staticmethod
    def response(message: Any, data: Any | None = None) -> None:
        Logger._log(LogLevel.INFO, message, data, log_type=LogType.RESPONSE)

    @staticmethod
    def _log(
        level: LogLevel,
        message: Any,
        data: Any | None = None,
        log_type: LogType | None = None,
    ) -> None:
        request_id = _request_id.get()
        formatted_id = f"({request_id}) " if request_id else ""
        colour = Logger._LEVEL_COLOURS.get(level, "")
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        prefix = f"[{timestamp}] {formatted_id}{colour}{level.value}\x1b[0m"
        if log_type is not None:
            prefix += f" [{log_type.value}]"

        print(prefix, message)
        if Logger._has_payload(data):
            try:
                payload = json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError):
                payload = str(data)
            print(prefix, payload)

    @staticmethod
    def _has_payload(data: Any | None) -> bool:
        if data is None:
            return False
        if isinstance(data, (str, bytes)):
            return bool(data)
        if isinstance(data, (list, tuple, set, dict)):
            return len(data) > 0
        return True

