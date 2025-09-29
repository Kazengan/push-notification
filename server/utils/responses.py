from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from .logger import Logger


def send_response(status_code: int, data: Any | None = None) -> Response:
    if isinstance(data, str):
        data = {"message": data}

    if data is None:
        data = {"status": "success" if status_code < 400 else "error"}

    Logger.response(status_code, data)

    return JSONResponse(status_code=status_code, content=data)

