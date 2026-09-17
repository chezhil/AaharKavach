import json
import os
import uuid
import datetime
import boto3

dynamodb = boto3.resource('dynamodb')
history_table = dynamodb.Table(os.environ.get('HISTORY_TABLE', 'AaharKavach-ScanHistory'))
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'AaharKavach-Profiles'))

def mock_role2_fetch_product(barcode):
    """Mocks Role 2 (Data) Open Food Facts lookup"""
    return {
        "barcode": barcode,
        "name": "Sample Peanut Butter",
        "ingredients": ["Peanuts", "Salt", "Palm Oil", "E120"],
        "confidence": "HIGH"
    }

def mock_role1_evaluate(product_data, profiles):
    """Mocks Role 1 (Agent) Strands evaluation"""
    evaluations = []
    for profile in profiles:
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
            ]
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
