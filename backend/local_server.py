#!/usr/bin/env python3
"""Local dev server for the AaharKavach API.

`sam local start-api` needs Docker. This serves the *same* handlers over plain
HTTP so the frontend can run against a real backend with nothing but Python:

    python backend/local_server.py            # http://localhost:3001

Then point the frontend at it:

    NEXT_PUBLIC_USE_MOCKS=false
    NEXT_PUBLIC_API_BASE_URL=http://localhost:3001

The Lambda handlers in ``src/*/app.py`` call the same ``shared.api`` functions,
so behaviour here matches what SAM deploys.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))            # data/, agent/
sys.path.insert(0, str(ROOT / "backend" / "src"))  # shared/

from shared import api  # noqa: E402


def _load_dotenv() -> None:
    """Read <repo>/.env into the environment if it exists.

    Keeps credentials out of git while still being zero-setup: drop a .env in
    the repo root and every run picks it up. Values already set in the
    environment win, so `GROQ_API_KEY=... ./dev.sh` still overrides.
    """
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("aahar")

PORT = int(os.environ.get("PORT", "3001"))

ROUTES = [
    ("GET", re.compile(r"^/api/profiles$")),
    ("POST", re.compile(r"^/api/profiles$")),
    ("PUT", re.compile(r"^/api/profiles/(?P<id>[^/]+)$")),
    ("DELETE", re.compile(r"^/api/profiles/(?P<id>[^/]+)$")),
    ("GET", re.compile(r"^/api/scan/barcode$")),
    ("POST", re.compile(r"^/api/scan/label$")),
    ("POST", re.compile(r"^/api/scan/url$")),
    ("POST", re.compile(r"^/api/evaluate$")),
    ("POST", re.compile(r"^/api/compare$")),
    ("GET", re.compile(r"^/api/history$")),
    ("GET", re.compile(r"^/api/explain$")),
    ("GET", re.compile(r"^/api/health$")),
]


def _parse_multipart(raw: bytes) -> tuple[str, bytes]:
    """Pull the filename and file content out of a multipart body.

    Small enough to do by hand: one file part, no nesting.
    """
    hit = re.search(rb'filename="([^"]*)"', raw)
    filename = hit.group(1).decode("utf-8", "replace") if hit else "label.jpg"

    # Content starts after the blank line ending this part's headers.
    split = raw.find(b"\r\n\r\n", hit.end() if hit else 0)
    if split == -1:
        return filename, b""
    body = raw[split + 4 :]

    # ...and ends at the closing boundary.
    boundary = re.match(rb"(--[^\r\n]+)", raw)
    if boundary:
        cut = body.find(b"\r\n" + boundary.group(1))
        if cut != -1:
            body = body[:cut]
    return filename, body


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # quieter default logging
        logger.info("%s %s", self.command, self.path.split("?")[0])

    # ---------------------------------------------------------- plumbing

    def _send(self, status: int, payload=None) -> None:
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type,X-Aahar-User,X-Aahar-Role,X-Aahar-Household",
        )

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _json_body(self) -> dict:
        raw = self._body()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except ValueError:
            raise api.ApiError(400, "Body is not valid JSON")

    def _caller(self) -> api.Caller:
        return api.Caller({k: v for k, v in self.headers.items()})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    # ---------------------------------------------------------- dispatch

    def _dispatch(self, method: str) -> None:
        url = urlparse(self.path)
        path, query = url.path.rstrip("/") or "/", parse_qs(url.query)

        try:
            status, payload = self._route(method, path, query)
        except api.ApiError as exc:
            self._send(exc.status, {"error": exc.message})
            return
        except Exception as exc:  # pragma: no cover - last resort
            logger.exception("Unhandled error on %s %s", method, path)
            self._send(500, {"error": str(exc)})
            return

        self._send(status, payload)

    def _route(self, method: str, path: str, query: dict):
        caller = self._caller()

        if method == "GET" and path == "/api/health":
            return 200, {"ok": True, "storage": "dynamodb" if os.environ.get("PROFILES_TABLE") else "local"}

        if path == "/api/profiles":
            if method == "GET":
                return api.list_profiles(caller)
            if method == "POST":
                return api.create_profile(caller, self._json_body())

        profile_match = re.match(r"^/api/profiles/(?P<id>[^/]+)$", path)
        if profile_match:
            profile_id = profile_match.group("id")
            if method == "PUT":
                return api.update_profile(caller, profile_id, self._json_body())
            if method == "DELETE":
                return api.remove_profile(caller, profile_id)

        if method == "GET" and path == "/api/scan/barcode":
            code = (query.get("code") or [""])[0]
            if not code:
                raise api.ApiError(400, "Pass ?code=<barcode>")
            return api.scan_barcode_endpoint(code)

        if method == "POST" and path == "/api/scan/url":
            return api.scan_url_endpoint(caller, self._json_body())

        if method == "POST" and path == "/api/scan/label":
            filename, image = _parse_multipart(self._body())
            return api.scan_label_endpoint(filename, image)

        if method == "POST" and path == "/api/evaluate":
            return api.evaluate_endpoint(caller, self._json_body())

        if method == "POST" and path == "/api/compare":
            return api.compare_endpoint(caller, self._json_body())

        if method == "GET" and path == "/api/history":
            return api.history_endpoint()

        if method == "GET" and path == "/api/explain":
            token = (query.get("ingredient") or [""])[0]
            if not token:
                raise api.ApiError(400, "Pass ?ingredient=<name>")
            return api.explain_endpoint(token)

        raise api.ApiError(404, f"No route for {method} {path}")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    logger.info("AaharKavach API on http://localhost:%d", PORT)
    logger.info("storage: %s", "DynamoDB" if os.environ.get("PROFILES_TABLE") else "local JSON")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
