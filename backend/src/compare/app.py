"""/api/compare — two products, side by side, for the active household."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import api  # noqa: E402
from shared.lambda_adapter import caller_from, json_body, respond, run  # noqa: E402


def lambda_handler(event, context):
    method = (event.get("httpMethod") or "POST").upper()
    if method == "OPTIONS":
        return respond(204, None)
    if method != "POST":
        return respond(405, {"error": "Method not allowed"})

    caller = caller_from(event)
    body = json_body(event)
    # Accept the older {"barcodes": [a, b]} spelling as well as the contract one.
    if "barcodes" in body and len(body.get("barcodes") or []) == 2:
        body = {
            "barcode_a": body["barcodes"][0],
            "barcode_b": body["barcodes"][1],
            "profile_ids": body.get("profile_ids") or body.get("active_profile_ids") or [],
        }
    return run(lambda: api.compare_endpoint(caller, body))
