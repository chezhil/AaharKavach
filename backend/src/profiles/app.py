"""/api/profiles — household management, gated by Cedar."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import api  # noqa: E402
from shared.lambda_adapter import caller_from, json_body, path_param, respond, run  # noqa: E402


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "GET").upper()
    caller = caller_from(event)

    if method == "OPTIONS":
        return respond(204, None)
    if method == "GET":
        return run(lambda: api.list_profiles(caller))
    if method == "POST":
        return run(lambda: api.create_profile(caller, json_body(event)))
    if method == "PUT":
        return run(lambda: api.update_profile(caller, path_param(event, "id"), json_body(event)))
    if method == "DELETE":
        return run(lambda: api.remove_profile(caller, path_param(event, "id")))
    return respond(405, {"error": "Method not allowed"})
