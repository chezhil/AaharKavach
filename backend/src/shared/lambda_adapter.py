"""Glue between API Gateway proxy events and the plain handlers in ``shared.api``.

Keeping this in one place means the four Lambda entry points stay three lines
each, and the local dev server can exercise identical logic without Docker.
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any, Callable

from . import api

logger = logging.getLogger(__name__)

CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Aahar-User,X-Aahar-Role,X-Aahar-Household",
}


class _DynamoJSONEncoder(json.JSONEncoder):
    """DynamoDB hands numbers back as Decimal; json can't serialise those."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


def respond(status: int, payload: Any) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": CORS,
        "body": "" if payload is None else json.dumps(payload, cls=_DynamoJSONEncoder),
    }


def caller_from(event: dict[str, Any]) -> api.Caller:
    return api.Caller(event.get("headers") or {})


def json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    try:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    except ValueError:
        raise api.ApiError(400, "Body is not valid JSON")


def query(event: dict[str, Any], key: str, default: str = "") -> str:
    params = event.get("queryStringParameters") or {}
    return str(params.get(key) or default)


def path_param(event: dict[str, Any], key: str) -> str:
    params = event.get("pathParameters") or {}
    value = params.get(key)
    if value:
        return str(value)
    # `sam local` sometimes omits pathParameters for greedy routes.
    match = re.search(rf"/([^/]+)$", event.get("path", ""))
    return match.group(1) if match else ""


def run(handler: Callable[[], tuple[int, Any]]) -> dict[str, Any]:
    """Execute a handler, mapping ApiError and crashes onto HTTP responses."""
    try:
        status, payload = handler()
        return respond(status, payload)
    except api.ApiError as exc:
        return respond(exc.status, {"error": exc.message})
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled error")
        return respond(500, {"error": "Internal server error"})
