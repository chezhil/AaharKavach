"""/api/history — reverse-chronological scans for the household."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import api  # noqa: E402
from shared.lambda_adapter import caller_from, respond, run  # noqa: E402


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "GET").upper()
    if method == "OPTIONS":
        return respond(204, None)
    if method != "GET":
        return respond(405, {"error": "Method not allowed"})
    caller = caller_from(event)
    return run(lambda: api.history_endpoint(caller))
