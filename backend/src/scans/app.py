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

    if method == "GET" and "explain" in path:
        ingredient = query(event, "ingredient")
        if not ingredient:
            return respond(400, {"error": "Pass ?ingredient=<name>"})
        return run(lambda: api.explain_endpoint(ingredient))

    if method == "POST" and "label" in path:
        import base64
        import re

        ctype = next((v for k, v in (event.get("headers") or {}).items() if k.lower() == "content-type"), "")
        if "application/json" in ctype:
            import binascii
            body = json_body(event)
            b64 = body.get("image_data", "")
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[-1]
            try:
                image_bytes = base64.b64decode(b64)
            except binascii.Error:
                return respond(400, {"error": "Malformed image data"})
            return run(lambda: api.scan_label_endpoint("capture.jpg", image_bytes))

        body = event.get("body") or ""
        # API Gateway base64-encodes binary bodies.
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(body)
        else:
            raw = body.encode("utf-8", "replace") if isinstance(body, str) else bytes(body)

        hit = re.search(rb'filename="([^"]*)"', raw)
        filename = hit.group(1).decode("utf-8", "replace") if hit else "label.jpg"

        image = b""
        if hit:
            split = raw.find(b"\r\n\r\n", hit.end())
            if split != -1:
                image = raw[split + 4 :]
                boundary = re.match(rb"(--[^\r\n]+)", raw)
                if boundary:
                    cut = image.find(b"\r\n" + boundary.group(1))
                    if cut != -1:
                        image = image[:cut]
        return run(lambda: api.scan_label_endpoint(filename, image))

    if method == "POST" and "url" in path:
        return run(lambda: api.scan_url_endpoint(caller, json_body(event)))

    if method == "POST" and "evaluate" in path:
        return run(lambda: api.evaluate_endpoint(caller, json_body(event)))

    return respond(405, {"error": "Method not allowed"})
