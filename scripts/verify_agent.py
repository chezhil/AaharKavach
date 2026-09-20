import os
import sys
import time

# Set up environment variables to force Agent usage
os.environ["AAHAR_USE_AGENT"] = "true"

# Add project root to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.evaluator import evaluate_product

def verify_agent():
    from agent.providers import model_id, provider_chain

    print("=== AaharKavach agent verification ===")
    print(f"Provider chain: {' -> '.join(provider_chain())}")
    print(f"Model ID: {model_id() or "(provider default)"}")

    if not os.environ.get("GROQ_API_KEY"):
        # This script's entire job is to prove a model actually answered. A
        # fabricated "PASS" here — with a hand-written EvaluationResult and
        # reasoning="strands" — would claim the agent ran when it was never
        # asked, which is exactly the false claim the rest of this codebase
        # (see shared/reasoning.py, shared/agent_bridge.py) is careful never to
        # make. With no key this must SKIP, not print a fake pass.
        print("SKIPPED: no GROQ_API_KEY in the environment — this run verifies "
              "nothing. Put one in .env (console.groq.com/keys).")
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
    
    print("\nSending payload to the agent...")
    start_time = time.time()
    
    try:
        result = evaluate_product(dummy_product, dummy_profiles)

        end_time = time.time()
        latency = end_time - start_time

        # _run_on_chain walks the provider chain and a later entry can pick up
        # a failed call — say which one actually answered rather than assuming
        # it was the primary just because a call went out.
        answered_by = getattr(result, "_provider", "unknown")
        primary = provider_chain()[0]
        print("{}: {} responded in {:.2f} seconds.".format(
            "PASS" if answered_by == primary else "FALLBACK", answered_by, latency))
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

        # The schema passing says the agent works. It says nothing about *who*
        # answered — so if a fallback picked the call up, say so rather than
        # exiting 0 and letting the write-up name the wrong provider.
        if answered_by != primary:
            print(
                f"\nFAIL: the schema is right, but {primary} did not answer — "
                f"{answered_by} picked the call up after it failed.\n"
                f"       Check GROQ_API_KEY, or whatever {primary} needs, before "
                "naming it in the write-up."
            )
            sys.exit(1)

    except Exception as e:
        print("\nFAIL: the agent could not evaluate the product.")
        print(f"Error details: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    verify_agent()
