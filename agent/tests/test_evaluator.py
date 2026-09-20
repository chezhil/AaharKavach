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


@patch("agent.evaluator.build_model", lambda provider=None: object())
@patch("agent.evaluator.Agent")
def test_evaluate_product_unwraps_structured_output(agent_cls, monkeypatch):
    monkeypatch.setenv("AAHAR_MODEL_PROVIDER", "groq")
    monkeypatch.delenv("AAHAR_MODEL_FALLBACK", raising=False)
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
    # And the result records which provider answered.
    assert getattr(result, "_provider", None) == "groq"


@patch("agent.evaluator.build_model", lambda provider=None: object())
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


@patch("agent.evaluator.build_model", lambda provider=None: object())
@patch("agent.evaluator.Agent")
def test_the_chain_moves_on_when_a_provider_fails_mid_call(agent_cls, monkeypatch):
    """A provider can build fine and then refuse or rate-limit the call.

    Retrying only construction would never reach the second provider, so the
    whole invocation is retried down the chain.
    """
    monkeypatch.setenv("AAHAR_MODEL_PROVIDER", "groq")
    monkeypatch.setenv("AAHAR_MODEL_FALLBACK", "ollama")

    expected = EvaluationResult(confidence="HIGH", profile_evaluations=[])
    calls = []

    def make_agent(*args, **kwargs):
        instance = MagicMock()

        def invoke(*a, **k):
            calls.append(1)
            if len(calls) == 1:          # first provider dies on invocation
                raise RuntimeError("429 rate_limit_exceeded")
            return MagicMock(structured_output=expected)

        instance.side_effect = invoke
        return instance

    agent_cls.side_effect = make_agent

    result = evaluate_product(PRODUCT, PROFILES)
    assert result is expected
    assert len(calls) == 2, "should have retried on the second provider"
    assert getattr(result, "_provider", None) == "ollama"
