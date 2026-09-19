"""Translation between each role's vocabulary and the canonical contract.

Role 2 speaks Open Food Facts (``product_name``, flat ingredient tokens).
Role 3 stores DynamoDB items (``householdId`` / ``profileId``).
The frontend speaks ``frontend/lib/types.ts``. Nothing else converts shapes —
if a field name has to change, it changes here.
"""

from __future__ import annotations

import re
from typing import Any

from data.client.openfoodfacts import ProductRecord
from data.mappings.descriptions import DESCRIPTIONS, DESCRIPTION_ALIAS_INDEX
from data.mappings.e_numbers import E_NUMBERS, ALIAS_INDEX as E_ALIAS_INDEX

from .contracts import (
    Confidence,
    Ingredient,
    Product,
    Profile,
    Restriction,
)

_E_BY_ID = {rec["additive_id"].upper(): rec for rec in E_NUMBERS}
_E_PATTERN = re.compile(r"\b(?:E|INS)\s*-?\s*(\d{3,4}[a-z]?)(?:\([ivx]+\))?\b", re.IGNORECASE)


def _norm(s: str) -> str:
    return " ".join(s.lower().strip().split())


def _e_number_for(token: str) -> str | None:
    """Pull an E-number out of an ingredient token, or resolve it by alias."""
    hit = _E_PATTERN.search(token)
    if hit:
        return f"E{hit.group(1).upper()}"
    alias = E_ALIAS_INDEX.get(_norm(token))
    if alias:
        return str(alias).upper() if str(alias).upper().startswith("E") else None
    return None


def _explainer_for(token: str, e_number: str | None) -> str | None:
    """Plain-language 'what is this', from Role 2's knowledge base."""
    key = DESCRIPTION_ALIAS_INDEX.get(_norm(token))
    if key and key in DESCRIPTIONS:
        return DESCRIPTIONS[key].get("plain_explanation")
    if e_number and e_number in _E_BY_ID:
        return _E_BY_ID[e_number].get("plain_explanation")
    return None


_ALL_CAPS_OR_DIGITS = re.compile(r"^[A-Z0-9][A-Z0-9\-]*$")


def _display_case(token: str) -> str:
    """Open Food Facts stores ingredients lower-case; the UI shows them raw.

    Title-case each word, but leave anything already capitalised or carrying a
    digit alone so "E322" and "70%" survive intact.
    """
    if not token.islower():
        return token
    words = []
    for word in token.split():
        if _ALL_CAPS_OR_DIGITS.match(word) or any(c.isdigit() for c in word):
            words.append(word.upper() if len(word) <= 5 else word)
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


# Open Food Facts leaves parser artefacts on some tokens: a leading asterisk
# for "may contain", stray underscores from its markup, empty brackets.
_ARTEFACTS = re.compile(r"^[\s*_\-–—\"'`]+|[\s*_\"'`]+$")
_MARKUP = re.compile(r"_+")


# Quantities and measurements that ride along in an ingredient list. "300ppm"
# came from "CAFFEINE 30mg/100ml (300ppm)" and rendered as its own ingredient.
_QUANTITY_ONLY = re.compile(
    r"^\(?\s*\d+(\.\d+)?\s*"
    r"(ppm|mg|g|kg|ml|l|%|kcal|kj|iu|mcg|µg)?"
    r"\s*(/\s*\d*\s*(g|ml|l|kg))?\s*\)?$",
    re.IGNORECASE,
)


def is_quantity(token: str) -> bool:
    """True for tokens that are a measurement, not an ingredient."""
    cleaned = token.strip().strip("()[] ")
    if not cleaned:
        return True
    if _QUANTITY_ONLY.match(cleaned):
        return True
    # Anything with no letters at all is not an ingredient name.
    return not any(c.isalpha() for c in cleaned)


def _tidy(token: str) -> str:
    cleaned = _MARKUP.sub(" ", token)
    cleaned = _ARTEFACTS.sub("", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    return " ".join(cleaned.split())


def ingredient_from_token(token: str) -> Ingredient:
    """One flat OFF token -> the object shape the UI renders."""
    clean = _display_case(_tidy(token))
    e_number = _e_number_for(clean)
    return Ingredient(
        name=clean,
        e_number=e_number,
        explainer=_explainer_for(clean, e_number),
    )


def _confidence(raw: str | None) -> Confidence:
    value = (raw or "").upper()
    return value if value in ("HIGH", "MEDIUM", "LOW") else "LOW"


def product_from_record(record: ProductRecord, confidence: str | None = None) -> Product:
    """Role 2 ``ProductRecord`` -> canonical ``Product``.

    The field renames are the whole point: ``product_name``->``name``,
    ``brands``->``brand``, ``confidence``->``data_confidence``, and flat
    ingredient strings become objects carrying their E-number and explainer.
    """
    return Product(
        barcode=record.barcode,
        name=record.product_name or f"Unknown product {record.barcode}",
        brand=record.brands or None,
        image_url=record.image_url,
        categories=list(record.categories or []),
        ingredients=[
            ingredient_from_token(t)
            for t in (record.ingredients or [])
            if t.strip() and not is_quantity(t)
        ],
        # Role 2 returns the score in a separate ConfidenceResult; the record's
        # own field is left at UNKNOWN, so the caller passes it in.
        data_confidence=_confidence(confidence or record.confidence),
        nutritional_stats=getattr(record, 'nutritional_stats', {}),
        source="OPEN_FOOD_FACTS",
    )


# ---------------------------------------------------------------- profiles

_ROLE_MAP = {"ADMIN": "ADMIN", "MEMBER": "MEMBER", "CHILD": "CHILD"}


def profile_from_item(item: dict[str, Any], *, can_edit: bool = True) -> Profile:
    """DynamoDB item (or local JSON row) -> canonical ``Profile``.

    Accepts both the canonical field names and Role 3's original
    ``profileId`` / ``allergies`` spelling, so previously-stored rows still load.
    """
    restrictions: list[Restriction] = []
    raw = item.get("restrictions") or item.get("allergies") or []
    for i, entry in enumerate(raw):
        if isinstance(entry, str):
            restrictions.append(Restriction(id=f"r{i}", label=entry, severity="MODERATE"))
        elif isinstance(entry, dict):
            restrictions.append(
                Restriction(
                    id=str(entry.get("id") or f"r{i}"),
                    label=str(entry.get("label") or entry.get("allergen") or "Unknown"),
                    severity=str(entry.get("severity", "MODERATE")).upper(),  # type: ignore[arg-type]
                )
            )

    role = str(item.get("household_role") or item.get("role") or "MEMBER").upper()
    return Profile(
        id=str(item.get("id") or item.get("profileId") or ""),
        name=str(item.get("name") or "Unnamed"),
        household_role=_ROLE_MAP.get(role, "MEMBER"),  # type: ignore[arg-type]
        restrictions=restrictions,
        accent=str(item.get("accent") or "teal"),
        can_edit=can_edit,
    )


def item_from_profile(profile: Profile, household_id: str, owner: str) -> dict[str, Any]:
    """Canonical ``Profile`` -> storage row, keeping Role 3's key schema."""
    return {
        "householdId": household_id,
        "profileId": profile.id,
        "id": profile.id,
        "name": profile.name,
        "owner": owner,
        "household_role": profile.household_role,
        "accent": profile.accent,
        "restrictions": [r.to_dict() for r in profile.restrictions],
    }
