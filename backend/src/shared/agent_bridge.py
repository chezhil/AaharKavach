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

#: Hard ceiling on a single model call, in seconds. Strands retries a rate
#: limited provider itself with exponential backoff and ignores the client's
#: max_retries, so on a throttled free tier one call can run until API Gateway
#: cuts the connection at 29s and the caller gets a 504 instead of a verdict.
#: This is the wall-clock stop: past it the call is abandoned and the
#: deterministic rulebook answers, which is the whole point of having one.
CALL_TIMEOUT_SECONDS = float(os.environ.get("AAHAR_AGENT_CALL_TIMEOUT", "10"))


def call_with_timeout(fn, *args, **kwargs):
    """Run `fn` but give up after CALL_TIMEOUT_SECONDS.

    The worker thread cannot be killed and is left to finish on its own; under
    Lambda the container is frozen after the response, so it costs nothing.
    Raising here lets the caller fall back rather than hang.
    """
    import concurrent.futures

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=CALL_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        raise TimeoutError(
            f"model call exceeded {CALL_TIMEOUT_SECONDS}s (provider slow or rate limited)"
        )
    finally:
        executor.shutdown(wait=False)


def agent_is_available() -> bool:
    """True when some model provider is installed and configured.

    Provider-agnostic on purpose: the same agent runs against Groq, Ollama or
    the Anthropic API, so the reasoning path is provable without any one
    vendor being reachable.
    """
    if os.environ.get("AAHAR_USE_AGENT", "").lower() != "true":
        return False
    try:
        from agent.providers import is_configured

        return is_configured()
    except ImportError:
        return False


def _product_payload(product: Product) -> dict[str, Any]:
    """Canonical Product -> plain JSON for the prompt.

    These are `Product`'s field names, not Role 2's ProductRecord ones. Passing
    `product_name`/`brands`/`is_found` here raised AttributeError, which the
    caller swallowed — so the agent silently never ran.
    """
    return {
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        # Ingredient is a dataclass; json.dumps cannot serialise it directly.
        "ingredients": [
            {"name": i.name, "e_number": i.e_number} for i in product.ingredients
        ],
        "confidence_score": product.data_confidence,
        "source": product.source,
    }


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

    # Say which vendor answered: with chaining on, "strands" alone hides the
    # fact that the primary provider was down and a fallback picked it up.
    provider = getattr(raw, "_provider", None)
    return EvaluationResult(
        confidence=str(data.get("confidence", "MEDIUM")).upper(),  # type: ignore[arg-type]
        profile_evaluations=parsed,
        safe_alternatives_suggestion=data.get("safe_alternatives_suggestion"),
        data_quality_note=data.get("data_quality_note"),
        reasoning=f"strands:{provider}" if provider else "strands",
    )


def evaluate_with_agent(
    product: Product,
    profiles: list[Profile],
    known_matches: Any = None,
) -> EvaluationResult | None:
    if not agent_is_available():
        logger.info("No model provider configured — skipping the agent")
        return None
    try:
        from agent.evaluator import evaluate_product
        raw = call_with_timeout(
            evaluate_product,
            _product_payload(product), _profiles_payload(profiles), known_matches,
        )
        return _coerce(raw, profiles)
    except Exception as exc:
        logger.warning("Agent evaluation failed: %s", exc)
        return None


def extract_webpage(webpage_text: str):
    """Transcribe a product page into name + ingredient strings, or None.

    Deliberately returns no verdict: the caller runs the extracted ingredients
    through the deterministic matcher, so page content cannot decide safety.
    """
    if not agent_is_available():
        logger.info("No model provider configured — cannot read product pages")
        return None
    try:
        from agent.evaluator import extract_product_from_webpage
        extraction = call_with_timeout(extract_product_from_webpage, webpage_text)
        if extraction is None or not getattr(extraction, "found_ingredients", False):
            return None
        return extraction
    except Exception as exc:
        logger.warning("Webpage extraction failed: %s", exc)
        return None


def explain_ingredient(token: str) -> str | None:
    """A short, plain-language explanation for an ingredient the curated
    knowledge base and the ontology fuzzy-match both came up empty on."""
    if not agent_is_available():
        logger.info("No model provider configured — cannot generate an explanation")
        return None
    try:
        from agent.evaluator import explain_ingredient as agent_explain
        result = call_with_timeout(agent_explain, token)
        text = (getattr(result, "explanation", "") or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("Ingredient explanation failed: %s", exc)
        return None
