#!/usr/bin/env python3
"""Verify a built SAM package would actually run in Lambda.

`sam build` only resolves pip dependencies. It cannot tell you that a handler
imports something living outside CodeUri, or that a data file is looked up at a
path that only exists in your checkout — both of which deploy cleanly and then
fail on every request.

This imports each handler with *only the package directory* on sys.path, the
way Lambda does, and exercises one request per function.

    cd backend && sam build && python ../scripts/check_lambda_package.py
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "backend" / ".aws-sam" / "build"

CHECKS = [
    (
        "AuthFunction",
        "auth.app",
        {
            "httpMethod": "POST",
            "path": "/api/auth/signin",
            "headers": {},
            "body": json.dumps({"email": "nobody@example.test", "password": "x"}),
        },
        # 401, not 200: there is no such account. What this proves is that the
        # handler imports, finds shared.api and the store, and answers — the
        # previous version 502'd on `from shared.store import save_profile`.
        401,
    ),
    ("ProfilesFunction", "profiles.app", {"httpMethod": "GET", "headers": {}}, 200),
    (
        "ScansFunction",
        "scans.app",
        {
            "httpMethod": "POST",
            "path": "/api/evaluate",
            "headers": {},
            "body": json.dumps(
                {"barcode": "8901063152762", "profile_ids": ["adult_1", "kid_1"]}
            ),
        },
        200,
    ),
    (
        "CompareFunction",
        "compare.app",
        {
            "httpMethod": "POST",
            "headers": {},
            "body": json.dumps(
                {
                    "barcode_a": "5000159461122",
                    "barcode_b": "8908003847412",
                    "profile_ids": ["kid_1"],
                }
            ),
        },
        200,
    ),
    ("HistoryFunction", "history.app", {"httpMethod": "GET"}, 200),
]

RUNNER = textwrap.dedent(
    """
    import importlib, json, os, sys
    # Lambda puts the task root on sys.path and nothing else from your machine.
    sys.path = [p for p in sys.path if "AaharKavach" not in p]
    sys.path.insert(0, os.getcwd())
    os.environ["AAHAR_STORAGE"] = "local"
    os.environ["AAHAR_LOCAL_DB"] = "/tmp/aahar-lambda-check.json"
    os.environ.pop("PROFILES_TABLE", None)

    module, event = sys.argv[1], json.loads(sys.argv[2])

    # sam build resolves wheels for the Lambda runtime (linux/x86_64), so a
    # package with native extensions cannot be fully exercised on a developer
    # machine. Record which ones refuse to load rather than letting them look
    # like an application fault: cedarpy failing to import makes Cedar fail
    # closed, and every profile request then answers 403.
    unloadable = []
    for native in ("cedarpy", "bcrypt"):
        try:
            importlib.import_module(native)
        except Exception as exc:
            unloadable.append(f"{native}: {type(exc).__name__}")

    handler = importlib.import_module(module).lambda_handler
    response = handler(event, None)
    print(json.dumps({
        "status": response["statusCode"],
        "body": response["body"][:300],
        "unloadable": unloadable,
    }))
    """
)


def main() -> int:
    if not BUILD.is_dir():
        print("No build found. Run `cd backend && sam build` first.", file=sys.stderr)
        return 2

    failures = 0
    skipped = 0
    for function, module, event, expected in CHECKS:
        package = BUILD / function
        if not package.is_dir():
            print(f"FAIL {function}: not built")
            failures += 1
            continue

        # The imports that only resolve in a developer checkout.
        for required in ("data", "agent", "shared", "policies"):
            if not (package / required).exists():
                print(f"FAIL {function}: '{required}' missing from the package")
                failures += 1

        proc = subprocess.run(
            [sys.executable, "-c", RUNNER, module, json.dumps(event)],
            cwd=package,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"FAIL {function}: handler raised\n{proc.stderr.strip()[-600:]}")
            failures += 1
            continue

        try:
            result = json.loads(proc.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            print(f"FAIL {function}: no parseable response\n{proc.stdout[-300:]}")
            failures += 1
            continue

        blocked = result.get("unloadable") or []
        if result["status"] != expected:
            if blocked:
                # Not a packaging fault: the wheel is correct for Lambda and
                # simply cannot run here. Say so instead of reporting a failure
                # the deployed stack will not have.
                print(
                    f"skip {function}: expected {expected}, got {result['status']} — "
                    f"can't verify on this host; {', '.join(blocked)} "
                    f"(built for the Lambda runtime, not "
                    f"{platform.machine()}/{platform.system()})"
                )
                skipped += 1
            else:
                print(f"FAIL {function}: expected {expected}, got {result['status']} — {result['body'][:160]}")
                failures += 1
        else:
            print(f"ok   {function}: {module} -> {result['status']}")

    if failures:
        print(f"\n{failures} problem(s). This package would fail after deploying.")
        return 1
    if skipped:
        print(
            f"\nPackage imports cleanly; {skipped} check(s) could not run on this "
            "host because a native wheel targets the Lambda runtime. Re-run in "
            "Linux/x86_64 (or after deploying) to exercise them."
        )
        return 0
    print("\nPackage looks deployable: every handler imports and answers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
