"""Route handlers, framework-free.

Each function takes plain Python and returns ``(status, payload)``. The Lambda
entry points in ``backend/src/*/app.py`` and the local dev server both call
these, so there is exactly one implementation of every endpoint.

Every response conforms to ``frontend/lib/types.ts``.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from . import catalogue, store
from .adapters import ingredient_from_token, product_from_record
from .cedar_utils import check_permission
from .contracts import (
    AlternativeProduct,
    EvaluationResult,
    Ingredient,
    Product,
    Profile,
    Restriction,
    ScanResult,
    worst_verdict,
)
from .reasoning import allergen_ids_for, evaluate

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class Caller:
    """Who is making the request.

    Cognito would populate this from the JWT authorizer. Until then it comes
    from optional headers so the demo can switch identity and show the Cedar
    rules actually biting.
    """

    def __init__(self, headers: dict[str, str] | None = None):
        h = {k.lower(): v for k, v in (headers or {}).items()}
        self.user_id = h.get("x-aahar-user", "user_123")
        self.role = h.get("x-aahar-role", "Admin")
        self.household = h.get("x-aahar-household", store.HOUSEHOLD_ID)


def _can_edit(caller: Caller, item: dict[str, Any]) -> bool:
    return check_permission(
        caller.user_id, caller.role, caller.household,
        "UpdateProfile", str(item.get("profileId", "")),
        str(item.get("owner", caller.user_id)), str(item.get("householdId", caller.household)),
    )


# ------------------------------------------------------------- profiles


def list_profiles(caller: Caller) -> tuple[int, Any]:
    if not check_permission(caller.user_id, caller.role, caller.household,
                            "ReadProfile", "any", caller.user_id, caller.household):
        raise ApiError(403, "Not allowed to read this household")
    items = store.list_profile_items()
    return 200, [
        store.profile_from_item(i, can_edit=_can_edit(caller, i)).to_dict() for i in items
    ]


def _profile_from_draft(draft: dict[str, Any], profile_id: str) -> Profile:
    restrictions = [
        Restriction(
            id=str(r.get("id") or f"r_{i}"),
            label=str(r.get("label", "")).strip(),
            severity=str(r.get("severity", "MODERATE")).upper(),  # type: ignore[arg-type]
        )
        for i, r in enumerate(draft.get("restrictions", []))
        if str(r.get("label", "")).strip()
    ]
    return Profile(
        id=profile_id,
        name=str(draft.get("name", "")).strip() or "Unnamed",
        household_role=str(draft.get("household_role", "MEMBER")).upper(),  # type: ignore[arg-type]
        restrictions=restrictions,
        accent=str(draft.get("accent", "teal")),
        can_edit=True,
    )


def create_profile(caller: Caller, draft: dict[str, Any]) -> tuple[int, Any]:
    profile_id = str(draft.get("id") or f"p_{uuid.uuid4().hex[:8]}")
    if not check_permission(caller.user_id, caller.role, caller.household,
                            "CreateProfile", profile_id, caller.user_id, caller.household):
        raise ApiError(403, "Only an admin can add someone to the household")
    profile = _profile_from_draft(draft, profile_id)
    store.put_profile(profile, owner=caller.user_id)
    return 201, profile.to_dict()


def update_profile(caller: Caller, profile_id: str, draft: dict[str, Any]) -> tuple[int, Any]:
    existing = store.get_profile_item(profile_id)
    if not existing:
        raise ApiError(404, f"No profile {profile_id}")
    if not check_permission(caller.user_id, caller.role, caller.household, "UpdateProfile",
                            profile_id, str(existing.get("owner", caller.user_id)),
                            str(existing.get("householdId", caller.household))):
        raise ApiError(403, "Household policy does not allow editing this profile")
    profile = _profile_from_draft(draft, profile_id)
    store.put_profile(profile, owner=str(existing.get("owner", caller.user_id)))
    return 200, profile.to_dict()


def remove_profile(caller: Caller, profile_id: str) -> tuple[int, Any]:
    existing = store.get_profile_item(profile_id)
    if not existing:
        raise ApiError(404, f"No profile {profile_id}")
    if not check_permission(caller.user_id, caller.role, caller.household, "DeleteProfile",
                            profile_id, str(existing.get("owner", caller.user_id)),
                            str(existing.get("householdId", caller.household))):
        raise ApiError(403, "Only an admin can remove someone from the household")
    store.delete_profile(profile_id)
    return 204, None


# ----------------------------------------------------------------- scan


def lookup_product(barcode: str) -> Product:
    """Open Food Facts first, bundled catalogue as the fallback."""
    barcode = str(barcode).strip()
    try:
        from data.services import scan_barcode

        context = scan_barcode(barcode)
        if context.product.is_found and context.product.ingredients:
            scored = context.confidence.to_dict()
            level = scored.get("confidence") or scored.get("level")
            return product_from_record(context.product, confidence=level)
        logger.info("OFF has no usable record for %s", barcode)
    except Exception as exc:
        logger.warning("Open Food Facts lookup failed for %s: %s", barcode, exc)

    fallback = catalogue.lookup(barcode)
    if fallback:
        return fallback
    raise ApiError(404, f"No product found for barcode {barcode}")


def scan_barcode_endpoint(barcode: str) -> tuple[int, Any]:
    return 200, lookup_product(barcode).to_dict()

def scan_url_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    """Smart QR: read a product page, then judge it ourselves.

    The model only transcribes the page. The verdict is computed from the
    household's restrictions by the same matcher every other scan uses, so a
    page cannot influence whether it is reported safe.
    """
    from .urlfetch import UnsafeUrl, fetch_text

    url = str(body.get("url", "")).strip()
    profiles = _resolve_profiles(caller, [str(p) for p in body.get("profile_ids", [])])

    try:
        text = fetch_text(url)
    except UnsafeUrl as exc:
        raise ApiError(400, str(exc))
    except Exception as exc:
        logger.warning("Could not fetch %s: %s", url, exc)
        raise ApiError(400, "Couldn't open that link — check the connection and try again")

    if not text:
        raise ApiError(422, "That page has no readable text")

    from .agent_bridge import BEDROCK_MODEL, extract_webpage

    # Distinguish "not configured" from "nothing on the page" — telling someone
    # a page has no ingredients when the reader is switched off sends them
    # hunting for the wrong problem.
    if os.environ.get("AAHAR_USE_AGENT", "").lower() != "true" or not BEDROCK_MODEL:
        raise ApiError(
            503,
            "Reading product pages needs the AI reader, which isn't switched on. "
            "Scan the barcode instead.",
        )

    extraction = extract_webpage(text)
    if extraction is None:
        raise ApiError(
            422, "We couldn't find an ingredient list on that page — try the barcode instead"
        )

    product = Product(
        barcode=url,
        name=extraction.product_name or "Product from page",
        brand=extraction.brand or None,
        ingredients=[ingredient_from_token(t) for t in extraction.ingredients if t.strip()],
        # Read off a webpage, not a verified record: never present as HIGH.
        data_confidence="LOW",
        source="URL",
    )
    if not product.ingredients:
        raise ApiError(
            422, "We couldn't find an ingredient list on that page — try the barcode instead"
        )

    evaluation = evaluate(product, profiles, _alternatives(product, profiles))

    scan = ScanResult(
        id=f"scan_{uuid.uuid4().hex[:8]}",
        scanned_at=store.now_iso(),
        product=product,
        evaluation=evaluation,
        profile_ids=[p.id for p in profiles],
    )
    store.record_scan(scan)
    return 200, scan.to_dict()

def scan_label_endpoint(filename: str) -> tuple[int, Any]:
    """Label-photo fallback.

    OCR/vision is Role 2's to add; until then this returns a low-confidence
    record so the whole path — and the confidence warning it triggers — is real
    and demonstrable rather than a dead button.
    """
    stem = (filename or "").rsplit(".", 1)[0] or "Photographed label"
    product = Product(
        barcode=f"photo_{uuid.uuid4().hex[:8]}",
        name=stem,
        brand=None,
        ingredients=[
            ingredient_from_token(t)
            for t in ("Refined Wheat Flour", "Milk Solids", "Soy Lecithin")
        ],
        data_confidence="LOW",
        source="LABEL_PHOTO",
    )
    return 200, product.to_dict()


def _alternatives(product: Product, profiles: list[Profile]) -> list[AlternativeProduct]:
    """Safer picks from the bundled catalogue — same category, clear for everyone."""
    category = product.categories[0] if product.categories else None
    if not category:
        return []
    out: list[AlternativeProduct] = []
    from .reasoning import evaluate_deterministic

    for candidate in catalogue.all_products():
        if candidate.barcode == product.barcode or category not in candidate.categories:
            continue
        result = evaluate_deterministic(candidate, profiles)
        if all(e.verdict == "SAFE" for e in result.profile_evaluations):
            out.append(
                AlternativeProduct(
                    barcode=candidate.barcode,
                    name=candidate.name,
                    brand=candidate.brand,
                    reason=f"No matches against {', '.join(p.name for p in profiles)}.",
                )
            )
        if len(out) == 3:
            break
    return out


def _product_from_payload(raw: dict[str, Any]) -> Product:
    return Product(
        barcode=str(raw.get("barcode", "")),
        name=str(raw.get("name", "Unknown product")),
        brand=raw.get("brand"),
        image_url=raw.get("image_url"),
        categories=list(raw.get("categories", [])),
        ingredients=[
            Ingredient(
                name=str(i.get("name", "")),
                e_number=i.get("e_number"),
                explainer=i.get("explainer"),
            )
            for i in raw.get("ingredients", [])
            if isinstance(i, dict) and i.get("name")
        ],
        data_confidence=str(raw.get("data_confidence", "LOW")).upper(),  # type: ignore[arg-type]
        source=str(raw.get("source", "MANUAL")),
    )


def _resolve_profiles(caller: Caller, profile_ids: list[str]) -> list[Profile]:
    profiles = store.load_profiles(profile_ids or None)
    if not profiles:
        raise ApiError(400, "Select at least one person to check against")
    return profiles


def evaluate_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    profile_ids = [str(p) for p in body.get("profile_ids", [])]
    profiles = _resolve_profiles(caller, profile_ids)

    if body.get("product"):
        product = _product_from_payload(body["product"])
    elif body.get("barcode"):
        product = lookup_product(str(body["barcode"]))
    else:
        raise ApiError(400, "evaluate needs a barcode or a product")

    result = evaluate(product, profiles, _alternatives(product, profiles))

    store.record_scan(
        ScanResult(
            id=f"scan_{uuid.uuid4().hex[:8]}",
            scanned_at=store.now_iso(),
            product=product,
            evaluation=result,
            profile_ids=[p.id for p in profiles],
        )
    )
    return 200, result.to_dict()


def _score(evaluation: EvaluationResult) -> int:
    total = 0
    for e in evaluation.profile_evaluations:
        total += 100 if e.verdict == "UNSAFE" else 10 if e.verdict == "CAUTION" else 0
        for f in e.flagged_ingredients:
            total += {"SEVERE": 5, "MODERATE": 3, "MILD": 1}[f.profile_severity]
    return total


def compare_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    barcode_a = str(body.get("barcode_a", "")).strip()
    barcode_b = str(body.get("barcode_b", "")).strip()
    if not barcode_a or not barcode_b:
        raise ApiError(400, "compare needs barcode_a and barcode_b")

    profiles = _resolve_profiles(caller, [str(p) for p in body.get("profile_ids", [])])

    def build(barcode: str) -> ScanResult:
        product = lookup_product(barcode)
        return ScanResult(
            id=f"cmp_{uuid.uuid4().hex[:8]}",
            scanned_at=store.now_iso(),
            product=product,
            evaluation=evaluate(product, profiles, _alternatives(product, profiles)),
            profile_ids=[p.id for p in profiles],
        )

    a, b = build(barcode_a), build(barcode_b)
    score_a, score_b = _score(a.evaluation), _score(b.evaluation)

    if score_a == score_b:
        safer, reason = "TIE", (
            "Both are clear for everyone you selected."
            if score_a == 0
            else "Both carry the same level of risk for the profiles you selected."
        )
    else:
        safer = "A" if score_a < score_b else "B"
        winner, loser = (a, b) if safer == "A" else (b, a)
        clean = all(e.verdict == "SAFE" for e in winner.evaluation.profile_evaluations)
        loser_flags = [f for e in loser.evaluation.profile_evaluations for f in e.flagged_ingredients]
        reason = (
            f"It clears every selected profile, while the other flags "
            f"{loser_flags[0].matched_allergen if loser_flags else 'a restriction'}."
            if clean
            else f"Fewer and less severe matches — the other flags "
                 f"{loser_flags[0].ingredient if loser_flags else 'an ingredient'}."
        )

    return 200, {"a": a.to_dict(), "b": b.to_dict(), "safer_pick": safer, "reason": reason}


def history_endpoint() -> tuple[int, Any]:
    return 200, store.list_history()


def explain_endpoint(token: str) -> tuple[int, Any]:
    ingredient = ingredient_from_token(token)
    if not ingredient.explainer:
        from data.services import resolve_ingredient

        matches = resolve_ingredient(token).get("matches", [])
        ingredient.explainer = next(
            (m.get("explanation") for m in matches if m.get("explanation")), None
        )
    return 200, ingredient.to_dict()
