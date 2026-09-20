"""Route handlers, framework-free.

Each function takes plain Python and returns ``(status, payload)``. The Lambda
entry points in ``backend/src/*/app.py`` and the local dev server both call
these, so there is exactly one implementation of every endpoint.

Every response conforms to ``frontend/lib/types.ts``.
"""

from __future__ import annotations

import logging
import os
import re
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
)
from .reasoning import evaluate

logger = logging.getLogger(__name__)


class _BudgetSpent(Exception):
    """Internal: the model budget is gone, fall through to the catalogue."""


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

    #: Cedar's policies compare `principal.role` to these exact strings, but
    #: the role arrives spelled three different ways: the profile store keeps
    #: "ADMIN", sign-up puts "Admin" in the JWT and sign-in puts the stored
    #: "ADMIN" in it. "ADMIN" != "Admin" in Cedar, so it failed closed and a
    #: signed-in user got 403 on their own household — signing *up* worked and
    #: signing *in* did not. Normalised here, once, for every entry point.
    _CEDAR_ROLES = {"admin": "Admin", "member": "Member", "child": "Child"}

    @classmethod
    def _role(cls, raw: str | None, fallback: str = "Admin") -> str:
        text = str(raw or "").strip()
        if not text:
            # Nothing was claimed at all — the header-less local demo default.
            return fallback
        # A role that *was* claimed but is not one Cedar knows is passed through
        # verbatim, so it matches no policy and Cedar denies. Mapping it onto a
        # known role here would be a way to spell "admin" wrong and be let in.
        return cls._CEDAR_ROLES.get(text.lower(), text)

    def __init__(self, headers: dict[str, str] | None = None):
        h = {k.lower(): v for k, v in (headers or {}).items()}
        self.user_id = h.get("x-aahar-user", "user_123")
        self.role = self._role(h.get("x-aahar-role"))
        
        if "x-aahar-household" in h:
            self.household = h["x-aahar-household"]
        else:
            self.household = store.HOUSEHOLD_ID
            
        self.token_payload = None

        auth_header = h.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                import jwt
                import os
                secret = os.environ.get("JWT_SECRET", "super_secret_dev_key")
                payload = jwt.decode(token, secret, algorithms=["HS256"])
                self.token_payload = payload
                # Use JWT claims if the header was omitted
                if "x-aahar-user" not in h:
                    self.user_id = payload.get("sub", self.user_id)
                if "x-aahar-role" not in h:
                    self.role = self._role(payload.get("role"), self.role)
                if "x-aahar-household" not in h:
                    self.household = payload.get("householdId", self.household)
            except Exception:
                pass


def signup_endpoint(draft: dict[str, Any]) -> tuple[int, Any]:
    email = str(draft.get("email") or "").strip()
    password = str(draft.get("password") or "")
    if not email or not password:
        raise ApiError(400, "Email and password are required")
        
    import bcrypt
    import uuid
    import datetime
    import jwt
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    household_id = f"hh_{uuid.uuid4().hex[:8]}"
    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    
    # Compute BMI: weight / ((height / 100) ** 2)
    weight = float(draft.get("weight") or draft.get("weight_kg") or 70.0)
    height = float(draft.get("height") or draft.get("height_cm") or 170.0)
    bmi = 0.0
    if height > 0:
        bmi = round(weight / ((height / 100) ** 2), 1)

    profile_draft = {
        "id": user_id,
        "name": str(draft.get("name") or email.split("@")[0]),
        "household_role": "ADMIN",
        "gender": str(draft.get("gender") or ""),
        "age": int(draft.get("age") or 30),
        "weight_kg": weight,
        "height_cm": height,
    }
    
    # Optional starting allergies
    allergies = draft.get("initial_allergies") or []
    if allergies:
        profile_draft["restrictions"] = [{"label": a, "severity": "MODERATE"} for a in allergies]
        
    profile = _profile_from_draft(profile_draft, user_id)
    # The store layer needs password_hash saved. 
    # For now, put_profile overwrites the item, so we save it with an extra kwarg or adapt.
    # We will just write a custom item for the admin profile to store the hash.
    item = store.item_from_profile(profile, household_id, user_id)
    item["password_hash"] = hashed
    item["email"] = email
    item["bmi"] = bmi
    # One call for both back-ends. The local branch used to assign into
    # `store._LOCAL` and call `store._save_local`, neither of which exists —
    # so every sign-up answered 500 with an AttributeError.
    store.put_profile_item(item)

    secret = os.environ.get("JWT_SECRET", "super_secret_dev_key")
    payload = {
        "sub": user_id,
        "email": email,
        "householdId": household_id,
        "role": "Admin",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    return 201, {
        "token": token,
        "user_id": user_id,
        "name": profile.name,
        "email": email,
        "household_id": household_id,
        "role": "admin",
        "biometrics": {
            "age": profile.age,
            "gender": profile.gender,
            "height": profile.height_cm,
            "weight": profile.weight_kg,
            "bmi": bmi
        }
    }


def signin_endpoint(draft: dict[str, Any]) -> tuple[int, Any]:
    email = str(draft.get("email") or "").strip()
    password = str(draft.get("password") or "")
    if not email or not password:
        raise ApiError(400, "Email and password required")
        
    # Scan for the user by email
    import bcrypt
    import jwt
    import datetime
    
    # A real deployment would put a GSI on email; the store scans instead,
    # which is fine at household scale and keeps both back-ends on one path.
    found_item = store.find_profile_item(email=email)

    if not found_item:
        raise ApiError(401, "Invalid email or password")
        
    hashed = str(found_item.get("password_hash") or "")
    try:
        ok = bool(hashed) and bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Malformed or absent hash — a seeded demo profile has no password at
        # all, and checkpw raises rather than returning False.
        ok = False
    if not ok:
        raise ApiError(401, "Invalid email or password")
        
    user_id = found_item.get("id") or found_item.get("profileId")
    household_id = found_item.get("householdId")
    
    secret = os.environ.get("JWT_SECRET", "super_secret_dev_key")
    payload = {
        "sub": user_id,
        "email": email,
        "householdId": household_id,
        "role": found_item.get("household_role", "Admin"),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    return 200, {
        "token": token,
        "user_id": user_id,
        "name": found_item.get("name"),
        "email": email,
        "household_id": household_id,
        "role": found_item.get("household_role", "Admin").lower(),
        "biometrics": {
            "age": found_item.get("age"),
            "gender": found_item.get("gender"),
            "height": found_item.get("height_cm"),
            "weight": found_item.get("weight_kg"),
            "bmi": found_item.get("bmi")
        }
    }


def me_endpoint(caller: Caller) -> tuple[int, Any]:
    if not caller.token_payload:
        raise ApiError(401, "Not authenticated")
    
    existing = store.get_profile_item(caller.user_id, household_id=caller.household)
    if not existing:
        raise ApiError(404, "User profile not found")
        
    return 200, {
        "user_id": caller.user_id,
        "name": existing.get("name"),
        "email": existing.get("email"),
        "household_id": caller.household,
        "role": existing.get("household_role", "Admin").lower(),
        "biometrics": {
            "age": existing.get("age"),
            "gender": existing.get("gender"),
            "height": existing.get("height_cm"),
            "weight": existing.get("weight_kg"),
            "bmi": existing.get("bmi")
        }
    }


def _can_edit(caller: Caller, item: dict[str, Any]) -> bool:
    return check_permission(
        caller.user_id, caller.role, caller.household,
        "UpdateProfile", str(item.get("profileId", "")),
        str(item.get("owner", caller.user_id)), str(item.get("householdId", caller.household)),
    )


def history_endpoint(caller: Caller) -> tuple[int, Any]:
    if not caller.household:
        raise ApiError(403, "Not allowed to read this household")
    return 200, store.list_history(household_id=caller.household)


def list_profiles(caller: Caller) -> tuple[int, Any]:
    if not check_permission(caller.user_id, caller.role, caller.household,
                            "ReadProfile", "any", caller.user_id, caller.household):
        raise ApiError(403, "Not allowed to read this household")
    items = store.list_profile_items(household_id=caller.household)
    return 200, [
        store.profile_from_item(i, can_edit=_can_edit(caller, i)).to_dict() for i in items
    ]


def _profile_from_draft(draft: dict[str, Any], profile_id: str) -> Profile:
    raw_restrictions = draft.get("restrictions") or []
    restrictions = []
    for i, r in enumerate(raw_restrictions):
        if not isinstance(r, dict):
            continue
        label = str(r.get("label") or "").strip()
        if not label or label.lower() == "none":
            continue
        restrictions.append(
            Restriction(
                id=str(r.get("id") or f"r_{i}"),
                label=label,
                severity=str(r.get("severity", "MODERATE")).upper(),  # type: ignore[arg-type]
            )
        )
    def _number(key: str, cast):
        """None unless the draft carries a usable value for this field."""
        raw = draft.get(key)
        if raw is None or raw == "":
            return None
        try:
            return cast(raw)
        except (TypeError, ValueError):
            return None

    gender = str(draft.get("gender") or "").strip().lower() or None
    if gender not in ("male", "female", "other"):
        gender = None

    return Profile(
        id=profile_id,
        name=str(draft.get("name", "")).strip() or "Unnamed",
        household_role=str(draft.get("household_role", "MEMBER")).upper(),  # type: ignore[arg-type]
        restrictions=restrictions,
        accent=str(draft.get("accent", "teal")),
        can_edit=True,
        # Carried, not dropped. These are what nutrition.calculate_daily_limits
        # works from, so losing them here meant the profile editor's age /
        # weight / height / gender inputs and the BMI they drive saved nothing,
        # and every household member silently fell back to default limits.
        age=_number("age", int),
        weight_kg=_number("weight_kg", float),
        height_cm=_number("height_cm", float),
        gender=gender,  # type: ignore[arg-type]
        tracked_nutrients=list(draft.get("tracked_nutrients") or [])
        or Profile.__dataclass_fields__["tracked_nutrients"].default_factory(),  # type: ignore[misc]
    )


def create_profile(caller: Caller, draft: dict[str, Any]) -> tuple[int, Any]:
    if not draft:
        raise ApiError(400, "Empty request body")
    profile_id = str(draft.get("id") or f"p_{uuid.uuid4().hex[:8]}")
    if not check_permission(caller.user_id, caller.role, caller.household,
                            "CreateProfile", profile_id, caller.user_id, caller.household):
        raise ApiError(403, "Only an admin can add someone to the household")
    profile = _profile_from_draft(draft, profile_id)
    store.put_profile(profile, owner=caller.user_id, household_id=caller.household)
    return 201, profile.to_dict()


def update_profile(caller: Caller, profile_id: str, draft: dict[str, Any]) -> tuple[int, Any]:
    if not draft:
        raise ApiError(400, "Empty request body")
    existing = store.get_profile_item(profile_id, household_id=caller.household)
    if not existing:
        raise ApiError(404, f"No profile {profile_id}")
    if not check_permission(caller.user_id, caller.role, caller.household, "UpdateProfile",
                            profile_id, str(existing.get("owner", caller.user_id)),
                            str(existing.get("householdId", caller.household))):
        raise ApiError(403, "Household policy does not allow editing this profile")
    profile = _profile_from_draft(draft, profile_id)
    store.put_profile(profile, owner=str(existing.get("owner", caller.user_id)), household_id=caller.household)
    return 200, profile.to_dict()


def remove_profile(caller: Caller, profile_id: str) -> tuple[int, Any]:
    existing = store.get_profile_item(profile_id, household_id=caller.household)
    if not existing:
        raise ApiError(404, f"No profile {profile_id}")
    if not check_permission(caller.user_id, caller.role, caller.household, "DeleteProfile",
                            profile_id, str(existing.get("owner", caller.user_id)),
                            str(existing.get("householdId", caller.household))):
        raise ApiError(403, "Only an admin can remove someone from the household")
    store.delete_profile(profile_id, household_id=caller.household)
    return 204, None


# ----------------------------------------------------------------- scan


def lookup_product(barcode: str) -> Product:
    """Open Food Facts first, bundled catalogue as the fallback."""
    barcode = str(barcode).strip()
    upstream_down = False

    # Open Food Facts rate-limits, and a rehearsal scans the same handful of
    # products over and over.
    from . import cache

    cache_key = cache.key_for("product", barcode)
    cached_product = cache.get("product", cache_key)
    if cached_product is not None:
        return _product_from_payload(cached_product)

    try:
        from data.client.openfoodfacts import OffApiError
        from data.services import scan_barcode

        try:
            context = scan_barcode(barcode)
        except OffApiError as exc:
            # Rate limit, timeout, 5xx — the product may well exist.
            logger.warning("Open Food Facts unavailable for %s: %s", barcode, exc)
            upstream_down = True
        else:
            if context.product.is_found and context.product.ingredients:
                scored = context.confidence.to_dict()
                level = scored.get("confidence") or scored.get("level")
                product = product_from_record(context.product, confidence=level)
                cache.put("product", cache_key, product.to_dict())
                return product
            logger.info("OFF has no usable record for %s", barcode)
    except Exception as exc:
        logger.warning("Product lookup failed for %s: %s", barcode, exc)
        upstream_down = True

    fallback = catalogue.lookup(barcode)
    if fallback:
        return fallback

    if upstream_down:
        # Saying "not in the database" here is wrong and sends people to
        # photograph a label when waiting would have worked.
        raise ApiError(
            503,
            "The product database isn't responding right now. Try again in a "
            "moment, or photograph the ingredients panel.",
        )
    raise ApiError(404, f"No product found for barcode {barcode}")


def scan_barcode_endpoint(barcode: str) -> tuple[int, Any]:
    return 200, lookup_product(barcode).to_dict()

def scan_url_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    """Smart QR: read a product page, then judge it ourselves.

    The model only transcribes the page. The verdict is computed from the
    household's restrictions by the same matcher every other scan uses, so a
    page cannot influence whether it is reported safe.
    """
    from .agent_bridge import start_request_budget
    from .urlfetch import UnsafeUrl, fetch_text

    start_request_budget()
    url = str(body.get("url", "")).strip()
    profile_ids = body.get("profile_ids") or []
    profiles = _resolve_profiles(caller, [str(p) for p in profile_ids])

    try:
        text = fetch_text(url)
    except UnsafeUrl as exc:
        raise ApiError(400, str(exc))
    except Exception as exc:
        logger.warning("Could not fetch %s: %s", url, exc)
        raise ApiError(400, "Couldn't open that link — check the connection and try again")

    if not text:
        raise ApiError(422, "That page has no readable text")

    from .agent_bridge import agent_is_available, extract_webpage

    # Distinguish "not configured" from "nothing on the page" — telling someone
    # a page has no ingredients when the reader is switched off sends them
    # hunting for the wrong problem.
    if not agent_is_available():
        raise ApiError(
            503,
            "Reading product pages needs the AI reader, which isn't switched on. "
            "Scan the barcode instead.",
        )

    try:
        extraction = extract_webpage(text)
    except TimeoutError as exc:
        logger.warning("Webpage extraction timed out: %s", exc)
        raise ApiError(
            503,
            "The reader is busy right now and couldn't finish that page. "
            "Try again in a moment, or scan the barcode instead.",
        )
    except Exception as exc:
        logger.warning("AI extraction failed: %s", exc)
        raise ApiError(503, "The AI reader is currently unavailable. Please try again later.")

    if extraction is None:
        raise ApiError(
            422, "We couldn't find an ingredient list on that page — try the barcode instead"
        )

    raw_ingredients = extraction.ingredients or []
    ingredients = [ingredient_from_token(t) for t in raw_ingredients if t and str(t).strip()]

    product = Product(
        barcode=url,
        name=extraction.product_name or "Product from page",
        brand=extraction.brand or None,
        ingredients=ingredients,
        # Read off a webpage, not a verified record: never present as HIGH.
        data_confidence="LOW",
        source="URL",
    )
    if not product.ingredients:
        raise ApiError(
            422, "We couldn't find an ingredient list on that page — try the barcode instead"
        )

    evaluation = _evaluate_with_alternatives(product, profiles)

    scan = ScanResult(
        id=f"scan_{uuid.uuid4().hex[:8]}",
        scanned_at=store.now_iso(),
        product=product,
        evaluation=evaluation,
        profile_ids=[p.id for p in profiles],
    )
    store.record_scan(scan, household_id=caller.household)
    return 200, scan.to_dict()

# Names a camera, screenshot tool or messaging app assigns on its own. None of
# them say anything about the product, so they must not become its title.
_CAMERA_ROLL_NAME = re.compile(
    r"""^(
        screenshot .* | screen\s?shot .* |
        (img|dsc|dscn|pxl|mvimg|gopr|photo|image|picture|pic|capture|scan|download)
            ([\s\-]* \d+)* |
        whatsapp\s(image|photo).* |
        signal-\d.* |
        \d+
    )$""",
    re.IGNORECASE | re.VERBOSE,
)


def _is_camera_roll_name(stem: str) -> bool:
    return bool(_CAMERA_ROLL_NAME.match(stem.strip()))


def scan_label_endpoint(filename: str, image_bytes: bytes = b"") -> tuple[int, Any]:
    """Read a photographed ingredients panel.

    OCR transcribes, a deterministic parser splits the list, and the verdict is
    computed later from the household's restrictions — so a misread label
    cannot influence whether something is reported safe.

    Confidence is capped at MEDIUM however clean the read: a photo of one
    packet is not a verified product record.
    """
    from .label_parse import parse_label
    from .ocr import OcrUnavailable, UnreadableImage, read_label

    if not image_bytes:
        raise ApiError(400, "No photo was uploaded")

    try:
        ocr = read_label(image_bytes)
    except UnreadableImage as exc:
        # The upload, not the server: saying "not set up" sends people to
        # debug the wrong thing.
        raise ApiError(422, f"{exc}. Upload a photo of the ingredients panel.")
    except OcrUnavailable as exc:
        logger.warning("OCR unavailable: %s", exc)
        raise ApiError(503, f"Label reading isn't set up on the server ({exc})")
    except Exception as exc:
        logger.warning("OCR failed: %s", exc)
        raise ApiError(422, "We couldn't read that photo. Try again with more light.")

    try:
        parsed = parse_label(ocr.text)
    except Exception as exc:
        logger.warning("Parse label failed: %s", exc)
        raise ApiError(422, "We couldn't parse the ingredients from that photo. Try a clearer image.")

    if not parsed.found_ingredients:
        raise ApiError(
            422,
            "We couldn't find an ingredient list in that photo — get the "
            "ingredients panel square in frame and try again.",
        )

    # An uploaded file's name is a decent fallback title ("oreo-label.jpg"),
    # but the camera path has no real filename, so it passes none rather than a
    # synthetic one — "capture.jpg" was reaching the UI as a product named
    # "capture" whenever OCR found no product name on the label.
    stem = (filename or "").rsplit(".", 1)[0].replace("_", " ").strip()
    # Whatever a phone or a screenshot tool named the file is not a product
    # name. "Screenshot 2026-09-18 at 10.59.32 AM" and "IMG 4821" both reached
    # the history list as product titles, which reads like the app failed.
    if _is_camera_roll_name(stem):
        stem = ""

    product = Product(
        barcode=f"photo_{uuid.uuid4().hex[:8]}",
        name=parsed.product_name or stem or "Photographed label",
        brand=None,
        ingredients=[ingredient_from_token(t) for t in parsed.ingredients],
        data_confidence=ocr.quality(),
        source="LABEL_PHOTO",
    )
    return 200, product.to_dict()


#: Swap It is skipped unless at least this much model time is left. The
#: verdict matters more than the suggestions, so the suggestions yield first.
SWAP_IT_MIN_BUDGET = 6.0


def _alternatives(
    product: Product, profiles: list[Profile]
) -> list[AlternativeProduct]:
    """Safer picks from the bundled catalogue or generated by Swap It 2.0 agent."""
    from .reasoning import evaluate_deterministic

    # If the product itself is SAFE, we don't need alternatives.
    prod_eval = evaluate_deterministic(product, profiles)
    if all(e.verdict == "SAFE" for e in prod_eval.profile_evaluations):
        return []

    category = product.categories[0] if product.categories else None
    candidates = []
    
    if category:
        for candidate in catalogue.all_products():
            if candidate.barcode == product.barcode or category not in candidate.categories:
                continue
            result = evaluate_deterministic(candidate, profiles)
            if all(e.verdict == "SAFE" for e in result.profile_evaluations):
                candidates.append(candidate)
            if len(candidates) == 5:
                break
                
    if os.environ.get("AAHAR_USE_AGENT", "").lower() == "true":
        from .agent_bridge import remaining_budget
        left = remaining_budget()
        skip = left is not None and left < SWAP_IT_MIN_BUDGET
        if skip:
            logger.info("Skipping Swap It: %.1fs of model budget left", left)
        try:
            if skip:
                raise _BudgetSpent
            from agent.evaluator import generate_swap_alternatives
            from .agent_bridge import call_with_timeout
            swap_result = call_with_timeout(
                generate_swap_alternatives,
                product.to_dict(),
                [p.to_dict() for p in profiles],
                [c.to_dict() for c in candidates],
            )
            out = []
            for alt in swap_result.alternatives:
                out.append(AlternativeProduct(
                    # A suggestion the model invented has no barcode. The UI
                    # keys off the synth_ prefix to hide "View details" and
                    # "Compare", which cannot work without a real product.
                    barcode=alt.barcode or f"synth_{uuid.uuid4().hex[:8]}",
                    name=alt.name,
                    brand=alt.brand,
                    reason=alt.reason or alt.why_it_works
                    or f"A safer pick for {', '.join(p.name for p in profiles)}.",
                    image_url=alt.image_url,
                    category=alt.category,
                    why_it_works=alt.why_it_works,
                    eliminated_allergens=alt.eliminated_allergens,
                    household_cleared=alt.household_cleared,
                    household_status=alt.household_status,
                    tags=alt.tags
                ))
            # Only when it actually found something. A terse model answering
            # with an empty list is not a reason to withhold the catalogue's
            # own safe picks, which is what returning `out` unconditionally did.
            if out:
                return out
        except _BudgetSpent:
            pass
        except Exception as exc:
            logger.warning("Swap It generation failed: %s", exc)

    # Fallback to deterministic alternatives
    out = []
    for candidate in candidates[:3]:
        out.append(
            AlternativeProduct(
                barcode=candidate.barcode,
                name=candidate.name,
                brand=candidate.brand,
                reason=f"No matches against {', '.join(p.name for p in profiles)}.",
            )
        )
    return out


def _product_from_payload(raw: dict[str, Any]) -> Product:
    return Product(
        barcode=str(raw.get("barcode", "")),
        name=str(raw.get("name", "Unknown product")),
        brand=raw.get("brand"),
        image_url=raw.get("image_url"),
        categories=list(raw.get("categories") or []),
        ingredients=[
            Ingredient(
                name=str(i.get("name", "")),
                e_number=i.get("e_number"),
                explainer=i.get("explainer"),
            )
            for i in (raw.get("ingredients") or [])
            if isinstance(i, dict) and i.get("name")
        ],
        data_confidence=str(raw.get("data_confidence", "LOW")).upper(),  # type: ignore[arg-type]
        source=str(raw.get("source", "MANUAL")),
        # The wire format is `nutritional_stats` — that is what Product.to_dict
        # emits and what the frontend type declares. Open Food Facts' own raw
        # `nutriments` key is still accepted for anything upstream that hands
        # the raw record straight over.
        nutritional_stats=raw.get("nutritional_stats") or raw.get("nutriments") or {},
    )


def _resolve_profiles(caller: Caller, profile_ids: list[str]) -> list[Profile]:
    # Scoped to the caller's household. Without it this always searched the
    # default household, so a signed-up user's own profile ids resolved to
    # nothing and every scan they ran came back 400 "Select at least one
    # person to check against" — with someone selected on screen.
    # An empty selection deliberately means "everyone in the household", not an
    # error: checking against more restrictions can only flag more, never fewer,
    # so it is the safe reading for an allergen app.
    profiles = store.load_profiles(profile_ids or None, household_id=caller.household)
    if not profiles:
        # Reaching here means the household itself is empty, or every id sent
        # belongs to another household — not that the caller forgot to choose.
        raise ApiError(
            400,
            "No one to check against — add someone to the household first.",
        )
    return profiles


def _evaluate_with_alternatives(product: Product, profiles: list[Profile]):
    """The verdict first, then the safer picks with whatever budget is left.

    Ordering matters twice over. Both calls draw on the same rate-limit quota
    and the same request budget, and Python evaluates arguments before the
    call — so writing evaluate(product, profiles, _alternatives(...)) ran Swap
    It *first*, let it spend the quota, and left the verdict to be throttled
    into the rulebook. The verdict is the product; the suggestions are a
    nicety, so the verdict goes first and the suggestions take the remainder.

    Alternatives are only attached to the result, never reasoned over, so
    computing them afterwards changes nothing about the answer.
    """
    evaluation = evaluate(product, profiles, [])
    evaluation.safe_alternatives = _alternatives(product, profiles)
    return evaluation


def evaluate_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    from .agent_bridge import start_request_budget

    start_request_budget()
    profile_ids = [str(p) for p in (body.get("profile_ids") or [])]
    profiles = _resolve_profiles(caller, profile_ids)

    if body.get("product"):
        product = _product_from_payload(body["product"])
    elif body.get("barcode"):
        product = lookup_product(str(body["barcode"]))
    else:
        raise ApiError(400, "evaluate needs a barcode or a product")

    result = _evaluate_with_alternatives(product, profiles)

    store.record_scan(
        ScanResult(
            id=f"scan_{uuid.uuid4().hex[:8]}",
            scanned_at=store.now_iso(),
            product=product,
            evaluation=result,
            profile_ids=[p.id for p in profiles],
        ),
        household_id=caller.household,
    )
    return 200, result.to_dict()


def _score(evaluation: EvaluationResult) -> int:
    total = 0
    for e in evaluation.profile_evaluations:
        total += 100 if e.verdict == "UNSAFE" else 10 if e.verdict == "CAUTION" else 0
        for f in (e.flagged_ingredients or []):
            total += {"SEVERE": 5, "MODERATE": 3, "MILD": 1}.get(f.profile_severity, 3)
    return total


def compare_endpoint(caller: Caller, body: dict[str, Any]) -> tuple[int, Any]:
    from .agent_bridge import start_request_budget

    start_request_budget()
    profiles = _resolve_profiles(caller, [str(p) for p in (body.get("profile_ids") or [])])

    def build(barcode: str | None, product_dict: dict[str, Any] | None) -> ScanResult:
        if product_dict:
            product = _product_from_payload(product_dict)
        elif barcode and barcode.strip():
            product = lookup_product(barcode.strip())
        else:
            raise ApiError(400, "compare needs either barcode or product object for both items")
            
        return ScanResult(
            id=f"cmp_{uuid.uuid4().hex[:8]}",
            scanned_at=store.now_iso(),
            product=product,
            evaluation=_evaluate_with_alternatives(product, profiles),
            profile_ids=[p.id for p in profiles],
        )

    a = build(body.get("barcode_a"), body.get("product_a"))
    b = build(body.get("barcode_b"), body.get("product_b"))
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


def explain_endpoint(token: str) -> tuple[int, Any]:
    ingredient = ingredient_from_token(token)
    resolved_via = "catalogue"
    if not ingredient.explainer:
        from data.services import resolve_ingredient

        enriched = resolve_ingredient(token)
        matches = enriched.get("matches", [])
        ingredient.explainer = next(
            (m.get("explanation") for m in matches if m.get("explanation")), None
        )
        if ingredient.explainer:
            resolved_via = enriched.get("source", "local")

    # Neither the curated tables nor the ontology's fuzzy match had this one.
    # Ask the model once, then remember the answer — the knowledge base only
    # covers ~199 entries, and the model bills per call.
    if not ingredient.explainer:
        cache_key = " ".join(token.lower().strip().split())
        cached = store.get_cached_explanation(cache_key)
        if cached:
            ingredient.explainer = cached
            resolved_via = "ai-cached"
        elif os.environ.get("AAHAR_USE_AGENT", "").lower() == "true":
            from .agent_bridge import explain_ingredient as agent_explain

            generated = agent_explain(token)
            if generated:
                store.put_cached_explanation(cache_key, generated, source="ai")
                ingredient.explainer = generated
                resolved_via = "ai"

    # Extra top-level key rather than a new Ingredient field: the TS contract in
    # frontend/lib/types.ts is frozen, and an unknown key is ignored there.
    return 200, {**ingredient.to_dict(), "resolved_via": resolved_via}


# API Gateway hard-caps a request at 29s and this endpoint is serial, so the
# basket has to fit inside that budget even on a cold start with slow lookups.
MAX_BATCH_ITEMS = 25


def audit_batch_endpoint(caller: Caller, body: dict[str, Any] | None) -> tuple[int, Any]:
    # Deliberately the deterministic rulebook, not `evaluate`: the matrix shows
    # verdicts and flagged ingredient names, all of which the rulebook produces.
    # The agent only adds prose this view never renders, and at ~5s per item it
    # blew the 29s gateway timeout at six items while burning one model call per
    # product in the basket.
    from .reasoning import evaluate_deterministic

    body = body or {}
    barcodes = body.get("barcodes", [])
    if not isinstance(barcodes, list) or not barcodes:
        raise ApiError(400, "barcodes list is required and must not be empty")
    if len(barcodes) > MAX_BATCH_ITEMS:
        raise ApiError(
            400, f"Too many items in one batch — {MAX_BATCH_ITEMS} is the limit."
        )

    household_id = body.get("household_id")
    if not household_id:
        if caller.household:
            household_id = caller.household
        else:
            raise ApiError(400, "household_id is required either in body or headers")
            
    # Resolve all profiles in this household
    household_profiles = store.load_profiles(household_id=household_id)
    if not household_profiles:
        raise ApiError(404, f"No profiles found for household {household_id}")

    items = []
    summary = {
        "total_items": len(barcodes),
        "all_family_safe_count": 0,
        "caution_count": 0,
        "unsafe_count": 0
    }

    for barcode in barcodes:
        try:
            product = lookup_product(str(barcode))
            result = evaluate_deterministic(product, household_profiles, [])
            
            # Determine household clearance
            member_verdicts = {}
            is_unsafe_for_any = False
            has_caution = False
            
            for eval_res in result.profile_evaluations:
                member_verdicts[eval_res.profile_id] = {
                    "name": eval_res.profile_name,
                    "verdict": eval_res.verdict,
                    "flagged_ingredients": [
                        {
                            "ingredient": flag.ingredient,
                            "reason": flag.matched_allergen
                        } for flag in (eval_res.flagged_ingredients or [])
                    ]
                }
                if eval_res.verdict == "UNSAFE":
                    is_unsafe_for_any = True
                elif eval_res.verdict == "CAUTION":
                    has_caution = True
            
            household_cleared = not is_unsafe_for_any
            
            if is_unsafe_for_any:
                summary["unsafe_count"] += 1
            elif has_caution:
                summary["caution_count"] += 1
            else:
                summary["all_family_safe_count"] += 1
                
            items.append({
                "barcode": product.barcode,
                "product_name": product.name,
                "brand": product.brand,
                "image_url": product.image_url,
                "household_cleared": household_cleared,
                "member_verdicts": member_verdicts,
                "status": "KNOWN"
            })
        except ApiError as e:
            items.append({
                "barcode": str(barcode),
                "status": "UNKNOWN" if e.status == 404 else "UNAVAILABLE"
            })
        except Exception as e:
            logger.error(f"Unexpected error processing barcode {barcode}: {e}")
            items.append({
                "barcode": str(barcode),
                "status": "ERROR"
            })

    return 200, {
        "summary": summary,
        "items": items
    }
