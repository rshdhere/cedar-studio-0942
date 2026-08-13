# Chat App

A real-time chat room built with Python 3 — no external dependencies.

## Features

- Join with a display name (stored in browser localStorage)
- Send and receive messages in real time via Server-Sent Events (SSE)
- Message history on join (last 200 messages)
- Responsive dark-theme UI

## Getting started

Requires Python 3.9+ (stdlib only — no pip install needed).

```bash
python3 app.py
```

Open [http://localhost:3000](http://localhost:3000).

Set `PORT` to change the listen port (default `3000`).

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat web UI |
| `/health` | GET | Health check `{"ok": true}` |
| `/api/messages` | GET | List message history |
| `/api/messages` | POST | Send a message `{"username", "text"}` |
| `/api/events` | GET | SSE stream for new messages |
