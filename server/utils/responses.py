from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse, Response

from .logger import Logger


def send_response(status_code: int, data: Any | None = None) -> Response:
    if isinstance(data, str):
        data = {"message": data}

    Logger.response(status_code, data)

    if data is None:
        return Response(status_code=status_code)

    return JSONResponse(status_code=status_code, content=data)

