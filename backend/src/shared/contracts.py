"""Canonical wire shapes for AaharKavach.

This is the Python mirror of ``frontend/lib/types.ts``. That file is the
published contract — the UI is built against it — so everything crossing the
network conforms to *this*, not to any one role's internal representation.

Each role keeps its own vocabulary internally:
  Role 1  EvaluationResult (pydantic)     — already matches this shape
  Role 2  ProductRecord / Match           — richer, OFF-shaped
  Role 3  DynamoDB items                  — householdId / profileId keys
Adapters in :mod:`shared.adapters` translate at the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

Severity = Literal["MILD", "MODERATE", "SEVERE"]
Verdict = Literal["SAFE", "CAUTION", "UNSAFE"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
HouseholdRole = Literal["ADMIN", "MEMBER", "CHILD"]

SEVERITY_ORDER: dict[str, int] = {"MILD": 1, "MODERATE": 2, "SEVERE": 3}


@dataclass
class Restriction:
    id: str
    label: str
    severity: Severity = "MODERATE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Profile:
    id: str
    name: str
    household_role: HouseholdRole = "MEMBER"
    restrictions: list[Restriction] = field(default_factory=list)
    accent: str = "teal"
    # Set from the Cedar decision for the *calling* user. The UI greys out
    # editing when this is false; it never decides this itself.
    can_edit: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "household_role": self.household_role,
            "restrictions": [r.to_dict() for r in self.restrictions],
            "accent": self.accent,
            "can_edit": self.can_edit,
        }


@dataclass
class Ingredient:
    name: str
    e_number: str | None = None
    explainer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Product:
    barcode: str
    name: str
    brand: str | None = None
    image_url: str | None = None
    categories: list[str] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    data_confidence: Confidence = "HIGH"
    source: str = "OPEN_FOOD_FACTS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "barcode": self.barcode,
            "name": self.name,
            "brand": self.brand,
            "image_url": self.image_url,
            "categories": self.categories,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "data_confidence": self.data_confidence,
            "source": self.source,
        }


@dataclass
class FlaggedIngredient:
    ingredient: str
    matched_allergen: str
    profile_severity: Severity
    explanation: str
    cross_reactive: bool = False
    # True when the model raised this but the knowledge base cannot corroborate
    # it. Shown separately and never allowed to drive the verdict, because a
    # claim with nothing behind it should not read like a matched allergen.
    unverified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProfileEvaluation:
    profile_id: str
    profile_name: str
    verdict: Verdict
    summary: str
    flagged_ingredients: list[FlaggedIngredient] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "verdict": self.verdict,
            "summary": self.summary,
            "flagged_ingredients": [f.to_dict() for f in self.flagged_ingredients],
        }


@dataclass
class AlternativeProduct:
    barcode: str
    name: str
    brand: str | None
    reason: str
    image_url: str | None = None
    category: str | None = None
    why_it_works: str | None = None
    eliminated_allergens: list[str] = field(default_factory=list)
    household_cleared: bool = False
    household_status: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    confidence: Confidence
    profile_evaluations: list[ProfileEvaluation] = field(default_factory=list)
    safe_alternatives_suggestion: str | None = None
    safe_alternatives: list[AlternativeProduct] = field(default_factory=list)
    data_quality_note: str | None = None
    # Which reasoning path produced this: "strands" or "deterministic".
    reasoning: str = "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "profile_evaluations": [e.to_dict() for e in self.profile_evaluations],
            "safe_alternatives_suggestion": self.safe_alternatives_suggestion,
            "safe_alternatives": [a.to_dict() for a in self.safe_alternatives],
            "data_quality_note": self.data_quality_note,
            "reasoning": self.reasoning,
        }


@dataclass
class ScanResult:
    id: str
    scanned_at: str
    product: Product
    evaluation: EvaluationResult
    profile_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scanned_at": self.scanned_at,
            "product": self.product.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "profile_ids": self.profile_ids,
        }


def worst_verdict(evals: list[ProfileEvaluation]) -> Verdict:
    if any(e.verdict == "UNSAFE" for e in evals):
        return "UNSAFE"
    if any(e.verdict == "CAUTION" for e in evals):
        return "CAUTION"
    return "SAFE"
