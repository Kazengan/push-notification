from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

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


@app.post("/")
async def create_notification(payload: NotificationPayload = Body(...)) -> Response:
    title = (payload.title or "").strip()
    if not title:
        return send_response(400, "'title' field is required")

    notification: Notification = {
        "id": str(uuid4()),
        "title": title,
        "message": payload.message,
        "url": payload.url,
        "icon": payload.icon,
        "color": payload.color,
        "createdAt": _timestamp(),
    }

    if payload.icon:
        encoded_icon = load_icon(payload.icon)
        if encoded_icon:
            notification["icon"] = encoded_icon

    notifications.append(notification)
    await broadcast(notification)

    return send_response(201)


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
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
    }

    response = StreamingResponse(event_generator(), media_type=None)
    response.init_headers(headers)
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

