"""Optional Strands path: Role 1's agent, converted to the canonical shape.

Enabled with ``AAHAR_USE_AGENT=true`` and only when the SDK imports and the
model responds. Everything here returns ``None`` rather than raising, so
:func:`shared.reasoning.evaluate` can fall back to the rulebook.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .contracts import (
    EvaluationResult,
    FlaggedIngredient,
    Product,
    Profile,
    ProfileEvaluation,
)

logger = logging.getLogger(__name__)

# Bedrock model ids are account- and region-specific, and the model has to be
# enabled in the console first. Keep it configurable rather than hard-coded.
BEDROCK_MODEL = os.environ.get("AAHAR_BEDROCK_MODEL", "")


def _profiles_payload(profiles: list[Profile]) -> list[dict[str, Any]]:
    return [
        {
            "profile_id": p.id,
            "profile_name": p.name,
            "restrictions": [
                {"allergen": r.label, "severity": r.severity} for r in p.restrictions
            ],
        }
        for p in profiles
    ]


def _coerce(raw: Any, profiles: list[Profile]) -> EvaluationResult | None:
    """Pydantic model / dict / JSON string -> canonical EvaluationResult."""
    if raw is None:
        return None
    if hasattr(raw, "model_dump"):
        data = raw.model_dump()
    elif isinstance(raw, dict):
        data = raw
    else:
        import json

        try:
            data = json.loads(str(raw))
        except (ValueError, TypeError):
            logger.warning("Agent returned an unparseable payload")
            return None

    evals = data.get("profile_evaluations")
    if not isinstance(evals, list) or not evals:
        return None

    by_id = {p.id: p for p in profiles}
    parsed: list[ProfileEvaluation] = []
    for entry in evals:
        if not isinstance(entry, dict):
            continue
        pid = str(entry.get("profile_id", ""))
        flags = [
            FlaggedIngredient(
                ingredient=str(f.get("ingredient", "")),
                matched_allergen=str(f.get("matched_allergen", "")),
                profile_severity=str(f.get("profile_severity", "MODERATE")).upper(),  # type: ignore[arg-type]
                explanation=str(f.get("explanation", "")),
                cross_reactive=bool(f.get("cross_reactive", False)),
            )
            for f in entry.get("flagged_ingredients", [])
            if isinstance(f, dict)
        ]
        parsed.append(
            ProfileEvaluation(
                profile_id=pid,
                profile_name=str(entry.get("profile_name") or getattr(by_id.get(pid), "name", "")),
                verdict=str(entry.get("verdict", "SAFE")).upper(),  # type: ignore[arg-type]
                summary=str(entry.get("summary", "")),
                flagged_ingredients=flags,
            )
        )

    if len(parsed) != len(profiles):
        # A scan checked against three people must return three verdicts.
        logger.warning("Agent returned %d/%d evaluations", len(parsed), len(profiles))
        return None

    return EvaluationResult(
        confidence=str(data.get("confidence", "MEDIUM")).upper(),  # type: ignore[arg-type]
        profile_evaluations=parsed,
        safe_alternatives_suggestion=data.get("safe_alternatives_suggestion"),
        data_quality_note=data.get("data_quality_note"),
        reasoning="strands",
    )


def evaluate_with_agent(product: Product, profiles: list[Profile]) -> EvaluationResult | None:
    if not BEDROCK_MODEL:
        logger.info("AAHAR_BEDROCK_MODEL is unset — skipping the agent")
        return None
    try:
        from agent.evaluator import evaluate_product
    except ImportError as exc:
        logger.info("Strands SDK unavailable: %s", exc)
        return None

    raw = evaluate_product(
        {
            "barcode": product.barcode,
            "name": product.product_name,
            "brand": product.brands,
            "ingredients": list(product.ingredients or []),
            "confidence_score": product.confidence,
            "is_found": product.is_found,
        }, 
        _profiles_payload(profiles)
    )
    return _coerce(raw, profiles)
