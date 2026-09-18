"""Cedar authorisation for household profiles.

Two fixes over the first cut:
  * the binding is ``cedarpy`` — ``cedarpolicy`` does not exist on PyPI, so the
    original import could never have resolved;
  * the policy file is located relative to *this file*, not the process working
    directory, which is not the repo root under Lambda or `sam local`.

In a deployed stack this is where you would swap in AWS Verified Permissions
(``boto3.client("verifiedpermissions").is_authorized``); the request shape
below is deliberately the same.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

POLICY_DIR = Path(__file__).resolve().parent.parent.parent / "policies"
POLICY_FILE = POLICY_DIR / "policies.cedar"

try:  # pragma: no cover - depends on the environment
    import cedarpy

    CEDAR_AVAILABLE = True
except ImportError:  # pragma: no cover
    cedarpy = None  # type: ignore[assignment]
    CEDAR_AVAILABLE = False


@lru_cache(maxsize=1)
def load_policies() -> str:
    return POLICY_FILE.read_text(encoding="utf-8")


def _entities(principal_id, principal_role, principal_household,
              resource_id, resource_owner, resource_household) -> list[dict]:
    entities = [
        {
            "uid": {"type": "AaharKavach::User", "id": principal_id},
            "attrs": {"role": principal_role, "householdId": principal_household},
            "parents": [],
        },
    ]
    # Only describe the owner separately when it is somebody else: a second
    # entity with the same uid overwrites the principal's role, which silently
    # demotes an Admin acting on a profile they own.
    if resource_owner != principal_id:
        entities.append(
            {
                "uid": {"type": "AaharKavach::User", "id": resource_owner},
                "attrs": {"role": "Member", "householdId": resource_household},
                "parents": [],
            }
        )
    entities.append(
        {
            "uid": {"type": "AaharKavach::Profile", "id": resource_id},
            "attrs": {
                "owner": {"__entity": {"type": "AaharKavach::User", "id": resource_owner}},
                "householdId": resource_household,
            },
            "parents": [],
        }
    )
    return entities


def check_permission(
    principal_id: str,
    principal_role: str,
    principal_household: str,
    action_name: str,
    resource_id: str,
    resource_owner: str,
    resource_household: str,
) -> bool:
    """True when Cedar permits this principal to take this action.

    Fails **closed** on any evaluation error: an authorisation layer that
    defaults to allow is worse than one that is briefly unavailable.
    """
    if not CEDAR_AVAILABLE:
        logger.warning("cedarpy is not installed — denying %s on %s", action_name, resource_id)
        return False

    request = {
        "principal": f'AaharKavach::User::"{principal_id}"',
        "action": f'AaharKavach::Action::"{action_name}"',
        "resource": f'AaharKavach::Profile::"{resource_id}"',
        "context": {},
    }
    entities = _entities(
        principal_id, principal_role, principal_household,
        resource_id, resource_owner, resource_household,
    )

    try:
        result = cedarpy.is_authorized(request, load_policies(), entities)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Cedar evaluation failed: %s", exc)
        return False

    decision = getattr(result, "decision", None)
    return str(getattr(decision, "value", decision)).lower() == "allow"
