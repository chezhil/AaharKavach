import logging
import json
from backend.src.shared.api import compare_endpoint, Product, Caller
from data.client.openfoodfacts import get_product

logging.basicConfig(level=logging.INFO)

# Valid barcodes
barcode_a = "5000159461122"  # Mars Bar or similar
barcode_b = "5060337500982"  # White Monster

print("Testing Barcode vs Barcode...")
caller = Caller({"X-Aahar-Household": "hh_test_runner"})
body = {
    "barcode_a": barcode_a,
    "barcode_b": barcode_b,
    "profile_ids": ["adult_1"]
}
status, response = compare_endpoint(caller, body)
assert status == 200, f"Expected 200 OK, got {status} {response}"
print(f"Barcode vs Barcode passed! Winner: {response['safer_pick']}")

print("Testing Barcode vs Product Payload...")
product_payload = get_product(barcode_b).to_dict()
# Simulate it came from OCR or Swap It, removing the barcode
product_payload["barcode"] = "synth_123"

body_mixed = {
    "barcode_a": barcode_a,
    "product_b": product_payload,
    "profile_ids": ["adult_1"]
}
status2, response2 = compare_endpoint(caller, body_mixed)
assert status2 == 200, f"Expected 200 OK, got {status2} {response2}"
print(f"Barcode vs Product Payload passed! Winner: {response2['safer_pick']}")
print("All tests passed!")
