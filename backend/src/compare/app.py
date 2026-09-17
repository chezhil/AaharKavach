import json
import boto3
import os

def mock_get_scan_result(barcode, profile_ids):
    # This would re-use the scans/app.py logic or Role1/Role2 directly
    return {
        "barcode": barcode,
        "name": f"Product {barcode}",
        "verdict": "SAFE" if barcode == "111" else "UNSAFE",
        "summary": "Safe to consume." if barcode == "111" else "Contains allergens."
    }

def lambda_handler(event, context):
    """
    Handles POST /api/compare
    """
    if event.get('httpMethod') != 'POST':
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}

    try:
        body = json.loads(event.get('body', '{}'))
        barcodes = body.get('barcodes', [])
        active_profile_ids = body.get('active_profile_ids', [])

        if len(barcodes) != 2:
            return {"statusCode": 400, "body": json.dumps({"error": "Exactly 2 barcodes required"})}

        # Fetch evaluations for both
        eval1 = mock_get_scan_result(barcodes[0], active_profile_ids)
        eval2 = mock_get_scan_result(barcodes[1], active_profile_ids)
        
        # Simple comparison logic (could be delegated to Role 1)
        recommendation = "Both are safe."
        if eval1['verdict'] == "SAFE" and eval2['verdict'] == "UNSAFE":
            recommendation = f"Choose {eval1['name']}."
        elif eval2['verdict'] == "SAFE" and eval1['verdict'] == "UNSAFE":
            recommendation = f"Choose {eval2['name']}."
        elif eval1['verdict'] == "UNSAFE" and eval2['verdict'] == "UNSAFE":
            recommendation = "Neither is safe for the active profiles."

        response_payload = {
            "comparison": [eval1, eval2],
            "recommendation": recommendation
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_payload)
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
