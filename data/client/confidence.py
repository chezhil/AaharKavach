"""Confidence scoring for product records.

This is THE data-quality signal that Role 1's agent surfaces directly in the
structured output `confidence` field and in `data_quality_note`.

We score a product record on several axes:

1.  Ingredient completeness   — is the full ingredient list present/parseable?
2.  Verified source           — is OFF 'complete', 'verified', 'to-be-completed'?
3.  Allergen tag coverage     — does the record carry allergen tags at all?
4.  Barcode sanity & age      — known barcode; presence of a photo reduces doubt.
5.  Brand completeness        — do we know the manufacturer?

Output: HIGH | MEDIUM | LOW + a human-readable reason list suitable for the
`data_quality_note` field in Role 1's structured output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


# OFF product status categories — high vs low 'verified' weight.
VERIFIED_STATUSES = {"complete", "verified"}
THIN_STATUSES = {"to-be-completed", "incomplete"}


@dataclass
class ConfidenceResult:
    level: str
    score: float  # 0..1 continuous score; level is derived from it
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"confidence": self.level, "score": self.score, "reasons": self.reasons}


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def score_record(record: Any) -> ConfidenceResult:
    """Score a normalized ProductRecord (any object with the record attrs).

    Accepts a duck-typed object: must expose `ingredients`, `ingredients_raw`,
    `allergens`, `off_status_verbose`, `is_found`, `barcode`, `image_url`,
    `brands`. Returns a ConfidenceResult container.
    """
    reasons: list[str] = []
    score = 1.0

    # 1) Found or not.
    if not record.is_found:
        return ConfidenceResult(
            LOW, 0.0,
            ["Product not found in Open Food Facts — full ingredient list unknown."],
        )

    # 2) Ingredient completeness (biggest weight).
    has_parsed = bool(record.ingredients)
    has_raw = bool(record.ingredients_raw)

    if has_parsed and len(record.ingredients) >= 3:
        score -= 0.05
        reasons.append(
            f"Complete ingredient list parsed ({len(record.ingredients)} ingredients)."
        )
    elif has_parsed:
        score -= 0.3
        reasons.append(
            f"Partial ingredient list ({len(record.ingredients)} ingredients) — may be incomplete."
        )
    elif has_raw:
        score -= 0.45
        reasons.append("Ingredient list present as raw text but could not be split reliably — double-check the label.")
    else:
        score -= 0.6
        reasons.append("No ingredient list available for this product — verify against the physical label.")

    # 3) Verification status from OFF.
    status = (record.off_status_verbose or "").lower()
    if status in VERIFIED_STATUSES:
        score -= 0.0
        reasons.append("Product entry is marked as verified/complete in Open Food Facts.")
    elif status in THIN_STATUSES:
        score -= 0.2
        reasons.append("Product entry is not fully verified on Open Food Facts.")
    elif not status:
        score -= 0.1
        reasons.append("Verification status unknown on Open Food Facts.")

    # 4) Allergen tags present? if not, flag.
    if record.allergens:
        reasons.append(f"Allergen tags present ({', '.join(record.allergens[:4])}).")
    else:
        score -= 0.25
        reasons.append("No allergen tags supplied — allergen data may be incomplete.")

    # 5) Brand completeness — knowing manufacturer is a proxy for data maturity.
    if not record.brands:
        score -= 0.1
        reasons.append("Product brand/manufacturer not listed — entry may be sparse.")

    # 6) Photo helps validate.
    if not record.image_url:
        score -= 0.05
        reasons.append("No product photo attached — visual verification isn't possible.")

    # Accumulated deductions shouldn't go below floor.
    score = _clamp(score)

    level = _level_for(score)
    return ConfidenceResult(level=level, score=score, reasons=reasons)


def _level_for(score: float) -> str:
    if score >= 0.75:
        return HIGH
    if score >= 0.45:
        return MEDIUM
    return LOW


def data_quality_note(result: ConfidenceResult) -> str:
    """Free-text note for Role 1's `data_quality_note` field."""
    if any("not found" in r.lower() for r in result.reasons):
        return ("Product not found in Open Food Facts — we couldn't verify its "
                "ingredients. Double-check the physical label before eating.")
    if result.level == HIGH:
        return "High-confidence product data — ingredient list looks complete and verified."
    if result.level == MEDIUM:
        return ("Medium confidence: some product data is thin — double-check the "
                "physical label before relying on this scan.")
    return ("Low confidence: product data is incomplete or unverified. This recommendation "
            "is a strong candidate for manual verification against the package label.")
