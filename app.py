"""Chat app server — zero external dependencies (stdlib only)."""

import json
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

messages: deque = deque(maxlen=200)
message_lock = threading.Lock()
sse_clients: list = []
sse_lock = threading.Lock()
next_id = 1


def broadcast_sse(msg: dict) -> None:
    with sse_lock:
        for pending in sse_clients:
            pending.append(msg)


class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, rel_path: str):
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        ext = os.path.splitext(rel_path)[1].lower()
        try:
            with open(rel_path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json({"ok": True})
        elif path == "/":
            self.serve_file("static/index.html")
        elif path == "/api/messages":
            with message_lock:
                data = list(messages)
            self.send_json(data)
        elif path == "/api/events":
            self.handle_sse()
        elif path.startswith("/static/"):
            self.serve_file(path[1:])
        else:
            self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/messages":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        text = (data.get("text") or "").strip()
        if not text:
            self.send_json({"error": "Message text required"}, 400)
            return
        username = (data.get("username") or "Anonymous").strip() or "Anonymous"
        global next_id
        with message_lock:
            msg = {
                "id": next_id,
                "username": username[:32],
                "text": text[:2000],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            next_id += 1
            messages.append(msg)
        broadcast_sse(msg)
        self.send_json(msg, 201)

    def handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        pending: list = []
        with sse_lock:
            sse_clients.append(pending)
        try:
            while True:
                batch = []
                with sse_lock:
                    if pending:
                        batch = list(pending)
                        pending.clear()
                for msg in batch:
                    line = f"data: {json.dumps(msg)}\n\n"
                    self.wfile.write(line.encode())
                    self.wfile.flush()
                self.wfile.write(b": keepalive\n\n")
                self.wfile.flush()
                time.sleep(0.5)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with sse_lock:
                try:
                    sse_clients.remove(pending)
                except ValueError:
                    pass


def main():
    port = int(os.environ.get("PORT", 3000))
    server = ThreadingHTTPServer(("0.0.0.0", port), ChatHandler)
    print(f"Chat server listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
