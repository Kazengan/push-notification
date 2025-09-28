# Push Notifications API (Python)

This project recreates the behaviour of the original [`push-notifications-api`](https://github.com/viktorholk/push-notifications-api) server in Python using [FastAPI](https://fastapi.tiangolo.com/). It exposes the same REST endpoints and Server-Sent Events (SSE) stream so it can be used as a drop-in replacement for the original Node.js implementation.

## Features

- REST API for publishing, listing, and retrieving notifications.
- Server-Sent Events stream for real-time delivery to connected clients.
- In-memory storage to mimic the reference implementation.
- Optional base64 icon loading from the bundled `server/icons` directory.
- Structured logging middleware mirroring the request/response tracing workflow from the original project.

## Requirements

- Python 3.10+
- Dependencies listed in [`requirements.txt`](./requirements.txt)

Install the dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Environment variables mirror the original project:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host interface the server should bind to. |
| `PORT` | `3000` | TCP port for the HTTP server. |

You can place a `.env` file in the project root to override these values.

## Running the server

After installing the dependencies, start the FastAPI application:

```bash
python -m server.main
```

The server logs the externally reachable URL on startup. When running locally the API will be available at <http://localhost:3000>.

## API Overview

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/` | Publish a notification. Requires a `title` field in the JSON body. |
| `GET` | `/` | Retrieve all notifications stored in memory. |
| `GET` | `/latest` | Fetch the most recently created notification. |
| `GET` | `/events` | Subscribe to notifications via SSE. |

### Sample request

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Launch",
    "message": "New version is live!",
    "icon": "rocket.png",
    "url": "https://example.com"
  }'
```

Connected SSE clients will immediately receive the notification payload, and it will be stored in the in-memory list for subsequent REST reads.

## Development

Run the built-in FastAPI server with auto-reload during development:

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 3000
```

## License

This repository is provided without an explicit license. Refer to the original project for its licensing details.
