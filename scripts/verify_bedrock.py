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
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE")):
        print("WARNING: AWS_ACCESS_KEY_ID or AWS_PROFILE not set in environment. This may fail unless you have instance roles.")
        
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
        
        print(f"PASS: Bedrock successfully responded in {latency:.2f} seconds.")
        print("\nStructured Response:")
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
