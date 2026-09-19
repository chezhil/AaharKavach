import json
import os
import uuid
import datetime
import boto3
import sys

# Add shared to path for AWS Lambda environment if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.nutrition import calculate_daily_limits

dynamodb = boto3.resource('dynamodb')
history_table = dynamodb.Table(os.environ.get('HISTORY_TABLE', 'AaharKavach-ScanHistory'))
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'AaharKavach-Profiles'))

def mock_role2_fetch_product(barcode):
    """Mocks Role 2 (Data) Open Food Facts lookup"""
    return {
        "barcode": barcode,
        "name": "Sample Peanut Butter",
        "ingredients": ["Peanuts", "Salt", "Palm Oil", "E120"],
        "nutriments": {
            "Energy_kcal": 588,
            "Protein": 25,
            "Carbs": 20,
            "Sugars": 9,
            "Fat": 50,
            "SatFat": 10,
            "Salt": 400,
            "Fiber": 6,
            "TransFat": 0
        },
        "confidence": "HIGH"
    }

def mock_role1_evaluate(product_data, profiles):
    """Mocks Role 1 (Agent) Strands evaluation"""
    evaluations = []
    nutriments = product_data.get('nutriments', {})
    
    for profile in profiles:
        # 1. Determine tracked nutrients (fallback to default 6 if missing)
        tracked = profile.get('tracked_nutrients', ["Energy_kcal", "Protein", "Carbs", "Sugars", "Fat", "Salt"])
        
        # 2. Calculate dynamic daily limits based on profile attributes
        limits = calculate_daily_limits(profile)
        
        # 3. Build nutrition response for this specific profile
        nutrition_res = {}
        for metric in tracked:
            nutrition_res[metric] = {
                "actual_value": nutriments.get(metric, 0),
                "daily_limit": limits.get(metric, 1)  # Fallback to 1 to prevent division by zero in UI
            }
            
        evaluations.append({
            "profile_id": profile['profileId'],
            "profile_name": profile.get('name', 'Unknown'),
            "verdict": "UNSAFE" if "Peanuts" in product_data['ingredients'] else "SAFE",
            "summary": "Product contains peanuts.",
            "flagged_ingredients": [
                {
                    "ingredient": "Peanuts",
                    "matched_allergen": "Peanut",
                    "profile_severity": "SEVERE",
                    "explanation": "Peanuts are a known severe allergen for this profile."
                }
            ],
            "nutrition": nutrition_res
        })
        
    return {
        "confidence": product_data["confidence"],
        "profile_evaluations": evaluations,
        "safe_alternatives_suggestion": "Try sunflower seed butter.",
        "data_quality_note": "Data looks complete."
    }

def lambda_handler(event, context):
    """
    Handles POST /api/scan/barcode and /api/evaluate
    """
    method = event.get('httpMethod')
    path = event.get('path', '')
    
    if method != 'POST':
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}

    try:
        body = json.loads(event.get('body', '{}'))
        active_profile_ids = body.get('active_profile_ids', [])
        barcode = body.get('barcode', 'unknown')
        
        # Mocking auth context
        principal_household = "hh_1"

        # 1. Fetch active profiles from DynamoDB
        profiles = []
        for pid in active_profile_ids:
            resp = profiles_table.get_item(Key={'householdId': principal_household, 'profileId': pid})
            if 'Item' in resp:
                profiles.append(resp['Item'])

        # 2. Forward to Role 2 (Product lookup)
        product_data = mock_role2_fetch_product(barcode)

        # 3. Forward to Role 1 (Agent Evaluation)
        evaluation_result = mock_role1_evaluate(product_data, profiles)

        # 4. Save to Scan History
        scan_id = str(uuid.uuid4())
        history_item = {
            'householdId': principal_household,
            'scanId': scan_id,
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'barcode': barcode,
            'productName': product_data['name'],
            'evaluation': evaluation_result
        }
        history_table.put_item(Item=history_item)

        response_payload = {
            "scanId": scan_id,
            "product": product_data,
            "result": evaluation_result
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_payload)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
