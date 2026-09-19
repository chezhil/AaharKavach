import json
import os
import boto3
from shared.cedar_utils import check_permission

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'AaharKavach-Profiles'))

def lambda_handler(event, context):
    """
    Handles API requests to /api/profiles.
    """
    method = event.get('httpMethod')
    
    # Mocking authenticated user context (In reality, extracted from Cognito/JWT Authorizer context)
    principal_id = "user_123"
    principal_role = "Admin"
    principal_household = "hh_1"
    
    if method == 'GET':
        # List profiles for household
        # Cedar Policy Check: Member can ReadProfile
        is_allowed = check_permission(principal_id, principal_role, principal_household, "ReadProfile", "any_profile", "any_owner", principal_household)
        if not is_allowed:
            return {"statusCode": 403, "body": json.dumps({"error": "Unauthorized"})}
            
        try:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('householdId').eq(principal_household)
            )
            return {
                "statusCode": 200,
                "body": json.dumps({"profiles": response.get('Items', [])})
            }
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
            
    elif method == 'POST':
        # Create a new profile
        body = json.loads(event.get('body', '{}'))
        new_profile_id = body.get('profileId')
        
        # Cedar Policy Check
        is_allowed = check_permission(principal_id, principal_role, principal_household, "CreateProfile", new_profile_id, principal_id, principal_household)
        if not is_allowed:
            return {"statusCode": 403, "body": json.dumps({"error": "Unauthorized. Only Admins can create profiles."})}
            
        try:
            item = {
                'householdId': principal_household,
                'profileId': new_profile_id,
                'name': body.get('name'),
                'owner': principal_id,
                'allergies': body.get('allergies', []),
                'age': body.get('age', 30),
                'weight_kg': body.get('weight_kg', 70.0),
                'height_cm': body.get('height_cm', 170.0),
                'gender': body.get('gender', 'male'),
                'tracked_nutrients': body.get('tracked_nutrients', ["Energy_kcal", "Protein", "Carbs", "Sugars", "Fat", "Salt"])
            }
            table.put_item(Item=item)
            return {"statusCode": 201, "body": json.dumps(item)}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
            
    return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
