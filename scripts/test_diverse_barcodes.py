import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:3001"
HEADERS = {
    "Content-Type": "application/json",
    "X-Aahar-Household": "hh_test_runner",
    "X-Aahar-User": "user_test",
    "X-Aahar-Role": "Admin"
}

def request(method, path, body=None, params=None):
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if body:
        req.data = json.dumps(body).encode("utf-8")
        
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

TEST_PRODUCTS = [
    {
        "name": "Maggi Masala Noodles",
        "barcode": "8901058851304",
        "expected_allergen": "Gluten / Wheat",
        "test_profile_restriction": "Gluten"
    },
    {
        "name": "Parle-G Biscuits",
        "barcode": "8901719101038",
        "expected_allergen": "Gluten & Dairy",
        "test_profile_restriction": "Dairy"
    },
    {
        "name": "Snickers Bar",
        "barcode": "5000159461122",
        "expected_allergen": "Peanuts",
        "test_profile_restriction": "Peanuts"
    },
    {
        "name": "Nutella",
        "barcode": "3017620422003",
        "expected_allergen": "Tree Nuts / Hazelnuts",
        "test_profile_restriction": "Tree Nuts"
    },
    {
        "name": "Coca-Cola",
        "barcode": "5449000000996",
        "expected_allergen": "None",
        "test_profile_restriction": "Peanuts"
    }
]

print("=== AaharKavach Multi-Barcode Verification ===\n")

for item in TEST_PRODUCTS:
    print(f"--- Testing {item['name']} ({item['barcode']}) ---")
    
    # 1. Create a temporary profile
    prof_id = f"test_{item['barcode']}"
    status, prof = request("POST", "/api/profiles", body={
        "id": prof_id,
        "name": f"Test {item['test_profile_restriction']}",
        "restrictions": [{"id": "r1", "label": item['test_profile_restriction'], "severity": "SEVERE"}],
        "tracked_nutrients": []
    })
    
    if status != 201:
        print(f"Failed to create profile: {status} {prof}")
        continue

    # 2. Lookup barcode
    status, product = request("GET", "/api/scan/barcode", params={"code": item["barcode"]})
    if status != 200:
        print(f"FAIL: Barcode lookup returned {status} - {product}")
        request("DELETE", f"/api/profiles/{prof_id}")
        continue
        
    print(f"  > Resolved: {product.get('name')} by {product.get('brand')}")
    
    # 3. Evaluate
    status, evaluation = request("POST", "/api/evaluate", body={
        "product": product,
        "profile_ids": [prof_id]
    })
    
    if status != 200:
        print(f"FAIL: Evaluate returned {status} - {evaluation}")
        request("DELETE", f"/api/profiles/{prof_id}")
        continue
        
    prof_eval = evaluation["profile_evaluations"][0]
    verdict = prof_eval["verdict"]
    flags = [f["ingredient"] for f in prof_eval.get("flagged_ingredients", [])]
    
    print(f"  > Target Restriction: {item['test_profile_restriction']}")
    print(f"  > Expected Allergen: {item['expected_allergen']}")
    print(f"  > Verdict: {verdict}")
    print(f"  > Flagged: {', '.join(flags) if flags else 'None'}")
    
    # 4. Swap It
    alts = evaluation.get("safe_alternatives", [])
    if verdict in ["UNSAFE", "CAUTION"]:
        print(f"  > Swap It Alternatives Found: {len(alts)}")
    
    # Clean up profile
    request("DELETE", f"/api/profiles/{prof_id}")
    
    if verdict == "UNSAFE" and item["expected_allergen"] != "None":
        print("  > PASS")
    elif verdict == "SAFE" and item["expected_allergen"] == "None":
        print("  > PASS")
    else:
        print("  > FAIL / MISMATCH (or caution)")
    print()

print("Verification complete.")
