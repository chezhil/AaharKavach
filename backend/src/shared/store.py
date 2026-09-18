"""Profiles and scan history, with a storage backend chosen at runtime.

DynamoDB when the tables are configured (deployed, or `sam local` against
DynamoDB Local); otherwise a JSON file on disk. The local backend is what makes
`npm run dev` + `python backend/local_server.py` work with nothing else
installed — no Docker, no AWS account.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import item_from_profile, profile_from_item
from .contracts import Profile, Restriction, ScanResult

HOUSEHOLD_ID = os.environ.get("AAHAR_HOUSEHOLD_ID", "hh_1")
LOCAL_DB = Path(os.environ.get("AAHAR_LOCAL_DB", Path(__file__).resolve().parents[2] / ".local-db.json"))

_lock = threading.Lock()


def _use_dynamo() -> bool:
    return bool(os.environ.get("PROFILES_TABLE")) and os.environ.get("AAHAR_STORAGE") != "local"


# ------------------------------------------------------------------ seed

SEED_PROFILES = [
    Profile(
        id="adult_1", name="Aaditya", household_role="ADMIN", accent="violet",
        restrictions=[Restriction("r1", "Gluten", "MODERATE"), Restriction("r2", "Soy", "MILD")],
    ),
    Profile(
        id="kid_1", name="Aryan", household_role="CHILD", accent="amber",
        restrictions=[Restriction("r3", "Peanuts", "SEVERE"), Restriction("r4", "Dairy", "MODERATE")],
    ),
    Profile(
        id="adult_2", name="Naman", household_role="MEMBER", accent="teal",
        restrictions=[Restriction("r5", "Latex", "MODERATE"), Restriction("r6", "Vegetarian", "MILD")],
    ),
]


def _blank() -> dict[str, Any]:
    return {
        "profiles": [item_from_profile(p, HOUSEHOLD_ID, "user_123") for p in SEED_PROFILES],
        "history": [],
    }


def _read_local() -> dict[str, Any]:
    if not LOCAL_DB.exists():
        data = _blank()
        _write_local(data)
        return data
    try:
        return json.loads(LOCAL_DB.read_text())
    except (OSError, ValueError):
        return _blank()


def _write_local(data: dict[str, Any]) -> None:
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_DB.write_text(json.dumps(data, indent=2, default=str))


def _tables():
    import boto3

    dynamodb = boto3.resource("dynamodb")
    return (
        dynamodb.Table(os.environ["PROFILES_TABLE"]),
        dynamodb.Table(os.environ.get("HISTORY_TABLE", "AaharKavach-ScanHistory")),
    )


# -------------------------------------------------------------- profiles


def list_profile_items() -> list[dict[str, Any]]:
    if _use_dynamo():
        from boto3.dynamodb.conditions import Key

        profiles_table, _ = _tables()
        resp = profiles_table.query(
            KeyConditionExpression=Key("householdId").eq(HOUSEHOLD_ID)
        )
        return list(resp.get("Items", []))
    with _lock:
        return list(_read_local()["profiles"])


def get_profile_item(profile_id: str) -> dict[str, Any] | None:
    return next((p for p in list_profile_items() if str(p.get("profileId")) == profile_id), None)


def put_profile(profile: Profile, owner: str = "user_123") -> Profile:
    item = item_from_profile(profile, HOUSEHOLD_ID, owner)
    if _use_dynamo():
        profiles_table, _ = _tables()
        profiles_table.put_item(Item=item)
        return profile
    with _lock:
        data = _read_local()
        data["profiles"] = [p for p in data["profiles"] if p.get("profileId") != profile.id]
        data["profiles"].append(item)
        _write_local(data)
    return profile


def delete_profile(profile_id: str) -> None:
    if _use_dynamo():
        profiles_table, _ = _tables()
        profiles_table.delete_item(Key={"householdId": HOUSEHOLD_ID, "profileId": profile_id})
        return
    with _lock:
        data = _read_local()
        data["profiles"] = [p for p in data["profiles"] if p.get("profileId") != profile_id]
        _write_local(data)


def load_profiles(profile_ids: list[str] | None = None, *, can_edit_for=None) -> list[Profile]:
    """Canonical profiles, optionally filtered to a selection."""
    items = list_profile_items()
    if profile_ids:
        wanted = set(profile_ids)
        items = [i for i in items if str(i.get("profileId")) in wanted]
    out = []
    for item in items:
        editable = True if can_edit_for is None else can_edit_for(item)
        out.append(profile_from_item(item, can_edit=editable))
    return out


# --------------------------------------------------------------- history


def record_scan(scan: ScanResult) -> None:
    item = {
        "householdId": HOUSEHOLD_ID,
        "scanId": scan.id,
        "timestamp": scan.scanned_at,
        "barcode": scan.product.barcode,
        "scan": scan.to_dict(),
    }
    if _use_dynamo():
        _, history_table = _tables()
        history_table.put_item(Item=item)
        return
    with _lock:
        data = _read_local()
        # One row per product — a re-scan replaces the older answer.
        data["history"] = [h for h in data["history"] if h.get("barcode") != scan.product.barcode]
        data["history"].insert(0, item)
        data["history"] = data["history"][:50]
        _write_local(data)


def list_history(limit: int = 50) -> list[dict[str, Any]]:
    if _use_dynamo():
        from boto3.dynamodb.conditions import Key

        _, history_table = _tables()
        resp = history_table.query(
            KeyConditionExpression=Key("householdId").eq(HOUSEHOLD_ID),
            ScanIndexForward=False,
            Limit=limit,
        )
        rows = list(resp.get("Items", []))
    else:
        with _lock:
            rows = list(_read_local()["history"])[:limit]
    rows.sort(key=lambda r: str(r.get("timestamp", "")), reverse=True)
    return [r["scan"] for r in rows if "scan" in r]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
