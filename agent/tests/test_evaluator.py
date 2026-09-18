from unittest.mock import patch, MagicMock

import pytest

# The Strands SDK is an optional dependency: the backend falls back to the
# deterministic rulebook without it, so the suite should skip rather than fail
# on a machine that has not installed agent/requirements.txt.
pytest.importorskip("strands", reason="pip install -r agent/requirements.txt")

from agent.evaluator import evaluate_product
from agent.models import EvaluationResult

# A mock test to show how to integrate with Role 3 backend
@patch("agent.evaluator.Agent")
@patch("agent.evaluator.get_product_data")
def test_evaluate_product(mock_get_product_data, mock_agent_class):
    # Setup mock product data
    mock_get_product_data.return_value = {
        "barcode": "12345",
        "ingredients": ["Sodium Caseinate", "Sugar"],
        "confidence_score": "HIGH"
    }
    
    # Setup mock agent response
    mock_agent_instance = MagicMock()
    mock_agent_instance.return_value = EvaluationResult(
        confidence="HIGH",
        profile_evaluations=[],
        safe_alternatives_suggestion="Try oat milk.",
        data_quality_note="Data is reliable."
    )
    mock_agent_class.return_value = mock_agent_instance
    
    # Test input
    profiles = [
        {"profile_id": "kid_1", "profile_name": "Aryan", "restrictions": [{"allergen": "Dairy", "severity": "SEVERE"}]}
    ]
    
    # Execute
    result = evaluate_product("12345", profiles)
    
    # Assert
    assert result.confidence == "HIGH"
    mock_get_product_data.assert_called_once_with("12345")
    mock_agent_instance.assert_called_once()
