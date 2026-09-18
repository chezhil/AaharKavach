from unittest.mock import MagicMock, patch

import pytest

# The Strands SDK is an optional dependency: the backend falls back to the
# deterministic rulebook without it, so the suite should skip rather than fail
# on a machine that has not installed agent/requirements.txt.
pytest.importorskip("strands", reason="pip install -r agent/requirements.txt")

from agent.evaluator import evaluate_product, extract_product_from_webpage
from agent.models import EvaluationResult, WebpageExtraction

PRODUCT = {
    "barcode": "12345",
    "name": "Test Cookies",
    "brand": "Britannia",
    "ingredients": [{"name": "Sodium Caseinate", "e_number": None}],
    "confidence_score": "HIGH",
}
PROFILES = [
    {
        "profile_id": "kid_1",
        "profile_name": "Aryan",
        "restrictions": [{"allergen": "Dairy", "severity": "SEVERE"}],
    }
]


def _agent_returning(structured):
    """Strands returns an AgentResult; the parsed model hangs off it."""
    instance = MagicMock()
    instance.return_value = MagicMock(structured_output=structured)
    cls = MagicMock(return_value=instance)
    return cls, instance


@patch("agent.evaluator.build_model", lambda: object())
@patch("agent.evaluator.Agent")
def test_evaluate_product_unwraps_structured_output(agent_cls):
    expected = EvaluationResult(
        confidence="HIGH",
        profile_evaluations=[],
        safe_alternatives_suggestion="Try oat milk.",
        data_quality_note="Data is reliable.",
    )
    cls, instance = _agent_returning(expected)
    agent_cls.side_effect = cls

    result = evaluate_product(PRODUCT, PROFILES)

    assert result is expected
    # The schema must be passed at call time, not construction.
    assert instance.call_args.kwargs["structured_output_model"] is EvaluationResult


@patch("agent.evaluator.build_model", lambda: object())
@patch("agent.evaluator.Agent")
def test_webpage_extraction_returns_ingredients_not_a_verdict(agent_cls):
    """The page reader transcribes; it must not be handed the verdict schema."""
    extraction = WebpageExtraction(
        product_name="Good Day Butter Cookies",
        brand="Britannia",
        ingredients=["Refined Wheat Flour", "Butter"],
        found_ingredients=True,
    )
    cls, instance = _agent_returning(extraction)
    agent_cls.side_effect = cls

    result = extract_product_from_webpage("<page text>")

    assert result.ingredients == ["Refined Wheat Flour", "Butter"]
    assert instance.call_args.kwargs["structured_output_model"] is WebpageExtraction
    # No allergen tools on the extractor — it has no reasoning job.
    assert agent_cls.call_args.kwargs["tools"] == []
