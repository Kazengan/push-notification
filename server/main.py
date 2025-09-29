from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError

from .icons.base64_icons import BASE64_ICONS
from .middleware.logger import LoggerMiddleware
from .utils.logger import Logger
from .utils.responses import send_response

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggerMiddleware)


class NotificationPayload(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


Notification = Dict[str, Any]
notifications: List[Notification] = []
clients: List[asyncio.Queue[Notification]] = []
clients_lock = asyncio.Lock()

def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


def load_icon(name: str) -> Optional[str]:
    if not name:
        return None

    normalized = name.strip()
    candidates = [normalized]
    if not normalized.lower().endswith(".png"):
        candidates.append(f"{normalized}.png")

    for candidate in candidates:
        icon = BASE64_ICONS.get(candidate)
        if icon:
            return icon

    Logger.error(f"Error loading icon {name}: file not found")
    return None


async def broadcast(notification: Notification) -> None:
    async with clients_lock:
        for queue in list(clients):
            await queue.put(notification)


async def _create_and_send(
    *,
    title: Optional[str],
    message: Optional[str] = None,
    url: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> tuple[bool, Notification | str]:
    title_clean = (title or "").strip()
    if not title_clean:
        return False, "'title' field is required"

    notification: Notification = {
        "id": str(uuid4()),
        "title": title_clean,
        "message": message,
        "url": url,
        "icon": icon,
        "color": color,
        "createdAt": _timestamp(),
    }

    if icon:
        encoded_icon = load_icon(icon)
        if encoded_icon:
            notification["icon"] = encoded_icon

    notifications.append(notification)
    await broadcast(notification)
    return True, notification


@app.post("/")
async def create_notification(payload: NotificationPayload = Body(...)) -> Response:
    success, result = await _create_and_send(
        title=payload.title,
        message=payload.message,
        url=payload.url,
        icon=payload.icon,
        color=payload.color,
    )
    if not success:
        return send_response(400, result)
    return send_response(201, result)


@app.get("/send")
async def create_notification_via_get(
    title: str,
    message: Optional[str] = None,
    url: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> Response:
    success, result = await _create_and_send(
        title=title,
        message=message,
        url=url,
        icon=icon,
        color=color,
    )
    if not success:
        return send_response(400, result)
    return send_response(200, result)


@app.get("/")
async def get_notifications() -> Response:
    return send_response(200, notifications)


@app.get("/latest")
async def get_latest_notification() -> Response:
    if not notifications:
        return send_response(404)
    return send_response(200, notifications[-1])


@app.get("/events")
async def stream_events(request: Request) -> StreamingResponse:
    queue: asyncio.Queue[Notification] = asyncio.Queue()

    async with clients_lock:
        clients.append(queue)
    client_host = request.client.host if request.client else "unknown"
    Logger.info(f"{client_host} connected")

    async def event_generator():
        try:
            yield "data: Connected\n\n"
            while True:
                notification = await queue.get()
                yield f"data: {json_dumps(notification)}\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            async with clients_lock:
                if queue in clients:
                    clients.remove(queue)
            Logger.info(f"{client_host} disconnected")

    # The Android client bundled with the reference implementation performs a
    # strict equality check on the Content-Type header, so we must send the
    # exact "text/event-stream" value without the usual charset suffix.
    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    # Starlette appends a charset to text media types by default which breaks the
    # Android client's strict equality check. Overwrite the header to the exact
    # value it expects and keep the connection open like the reference Node server.
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    return response


def json_dumps(data: Any) -> str:
    import json

    return json.dumps(data, ensure_ascii=False)


def _get_ip_address() -> str:
    import socket

    if (host := os.getenv("HOST")) and host != "0.0.0.0":
        return host

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            return ip_address
    except OSError:
        return "127.0.0.1"


def run() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))

    visible_host = _get_ip_address() if host == "0.0.0.0" else host
    Logger.info(f"Server is running on http://{visible_host}:{port}")

    uvicorn.run("server.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    Logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail) if exc.detail else "HTTP error",
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    Logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid request payload",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    Logger.exception(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc),
            "path": request.url.path,
        },
    )
