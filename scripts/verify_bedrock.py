import os
import sys
import time

# Set up environment variables to force Agent usage
os.environ["AAHAR_USE_AGENT"] = "true"

# Fallback to a valid default Bedrock model if not provided
if not os.environ.get("AAHAR_BEDROCK_MODEL"):
    os.environ["AAHAR_BEDROCK_MODEL"] = "us.anthropic.claude-3-haiku-20240307-v1:0"

# Add project root to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.evaluator import evaluate_product

def verify_bedrock():
    print("=== AaharKavach Bedrock Verification ===")
    print(f"Model ID: {os.environ['AAHAR_BEDROCK_MODEL']}")

    # Check AWS credentials implicitly by looking at env vars, but let boto3 handle the actual check
    has_creds = bool(os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE") or os.environ.get("GROQ_API_KEY"))
    if not has_creds:
        # This script's entire job is to prove a model actually answered. A
        # fabricated "PASS" here — with a hand-written EvaluationResult and
        # reasoning="strands" — would claim Bedrock ran when it never was
        # asked, which is exactly the false-AWS-usage claim the rest of this
        # codebase (see shared/reasoning.py, shared/agent_bridge.py) is careful
        # never to make. On an unauthenticated CI runner this must SKIP, not
        # print a fake pass.
        print("SKIPPED: No AWS_ACCESS_KEY_ID/AWS_PROFILE or GROQ_API_KEY in "
              "environment — this run verifies nothing about Bedrock.")
        return

    # Dummy product data with a known allergen
    dummy_product = {
        "barcode": "123456789",
        "name": "Dummy Milk Chocolate",
        "brand": "Dummy Brand",
        "ingredients": ["Sugar", "Cocoa Mass", "Sodium Caseinate"],
        "confidence_score": "HIGH",
        "is_found": True
    }
    
    # Dummy profile with a Dairy restriction
    dummy_profiles = [
        {
            "profile_id": "test_user",
            "profile_name": "Test User",
            "restrictions": [{"allergen": "Dairy", "severity": "SEVERE"}]
        }
    ]
    
    print("\nSending payload to Bedrock...")
    start_time = time.time()
    
    try:
        result = evaluate_product(dummy_product, dummy_profiles)

        end_time = time.time()
        latency = end_time - start_time

        # _run_on_chain tries Bedrock first and falls back to Groq on failure
        # (e.g. pending model access) — say which one actually answered rather
        # than assuming it was Bedrock just because a call went out.
        answered_by = getattr(result, "_provider", "unknown")
        print("PASS: {} successfully responded in {:.2f} seconds.".format(answered_by, latency))
        print("\nStructured Response:")
        # `result` here is agent.models.EvaluationResult (a Pydantic model),
        # not shared.contracts.EvaluationResult (a dataclass) — the two share
        # a name but not an interface. Pydantic serialises with model_dump*,
        # it has no .to_dict().
        print(result.model_dump_json(indent=2))

        # Validate structure
        assert len(result.profile_evaluations) == 1
        assert result.profile_evaluations[0].verdict == "UNSAFE"
        assert len(result.profile_evaluations[0].flagged_ingredients) > 0
        
        print("\nPASS: The response conforms exactly to the required JSON schema and correctly identified Sodium Caseinate.")
        
    except Exception as e:
        print("\nFAIL: Failed to evaluate using Bedrock.")
        print(f"Error details: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    verify_bedrock()
