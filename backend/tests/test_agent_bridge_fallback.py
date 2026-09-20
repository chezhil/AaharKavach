import pytest
from unittest.mock import patch
from shared import agent_bridge

def test_extract_webpage_graceful_fallback():
    with patch("shared.agent_bridge.agent_is_available", return_value=True):
        with patch("agent.evaluator.extract_product_from_webpage", side_effect=Exception("the model provider went down")):
            result = agent_bridge.extract_webpage("<html>Some random text</html>")
            assert result is None, "The bridge should swallow the exception and return None"

def test_evaluate_with_agent_graceful_fallback():
    from shared.contracts import Product, Profile
    with patch("shared.agent_bridge.agent_is_available", return_value=True):
        with patch("agent.evaluator.evaluate_product", side_effect=Exception("Model limit reached")):
            product = Product("123", "Test", [], "LOW", "URL")
            result = agent_bridge.evaluate_with_agent(product, [])
            assert result is None, "The bridge should swallow the exception and return None"
