"""/api/auth/* — sign-up, sign-in and the current session.

Three lines per route, like every other entry point: the logic lives in
``shared.api`` so the deployed Lambda and ``backend/local_server.py`` run
exactly the same code.

The first version of this module re-implemented sign-up here instead, and the
two drifted apart immediately — it imported ``save_profile`` from the store,
which does not exist (so the function 502'd on import), it had no sign-in route
at all, and its local branch was a bare ``pass`` that saved nothing. It was
also mounted on /api/signup and /api/login while the frontend calls
/api/auth/signup and /api/auth/signin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import api  # noqa: E402
from shared.lambda_adapter import caller_from, json_body, respond, run  # noqa: E402


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "POST").upper()
    path = event.get("path", "")

    if method == "OPTIONS":
        return respond(204, None)

    if method == "POST" and path.endswith("/signup"):
        return run(lambda: api.signup_endpoint(json_body(event)))

    if method == "POST" and (path.endswith("/signin") or path.endswith("/login")):
        return run(lambda: api.signin_endpoint(json_body(event)))

    if method == "GET" and path.endswith("/me"):
        return run(lambda: api.me_endpoint(caller_from(event)))

    return respond(405, {"error": "Method not allowed"})
