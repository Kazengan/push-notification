from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.logger import Logger


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        token = Logger.bind_request_id(request_id)
        try:
            body_bytes = await request.body()
            # store the body for downstream handlers
            if body_bytes:
                setattr(request, "_body", body_bytes)
            else:
                setattr(request, "_body", b"")

            parsed_body: Any | None = None
            if body_bytes:
                try:
                    parsed_body = json.loads(body_bytes.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    parsed_body = body_bytes.decode(errors="ignore")

            Logger.request(f"{request.method} {request.url.path}", parsed_body)

            response = await call_next(request)
            return response
        finally:
            Logger.reset_request_id(token)

