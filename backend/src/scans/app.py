"""/api/scan/* and /api/evaluate — real lookup, real reasoning.

The first cut answered from `mock_role2_fetch_product` and `mock_role1_evaluate`
inlined here. Both now go through `shared.api`, which calls Role 2's Open Food
Facts client and the reasoning layer (Role 1's agent when enabled).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import api  # noqa: E402
from shared.lambda_adapter import caller_from, json_body, query, respond, run  # noqa: E402


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "POST").upper()
    path = event.get("path", "")
    caller = caller_from(event)

    if method == "OPTIONS":
        return respond(204, None)

    if method == "GET" and "barcode" in path:
        return run(lambda: api.scan_barcode_endpoint(query(event, "code")))

    if method == "POST" and "label" in path:
        body = event.get("body") or ""
        raw = body.encode("utf-8", "replace") if isinstance(body, str) else bytes(body)
        import re

        hit = re.search(rb'filename="([^"]*)"', raw)
        filename = hit.group(1).decode("utf-8", "replace") if hit else "label.jpg"
        return run(lambda: api.scan_label_endpoint(filename))

    if method == "POST":
        return run(lambda: api.evaluate_endpoint(caller, json_body(event)))

    return respond(405, {"error": "Method not allowed"})
