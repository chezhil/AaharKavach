import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
history_table = dynamodb.Table(os.environ.get('HISTORY_TABLE', 'AaharKavach-ScanHistory'))

def lambda_handler(event, context):
    """
    Handles GET /api/history
    """
    if event.get('httpMethod') != 'GET':
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}

    try:
        # Mocking auth context
        principal_household = "hh_1"

        # Query DynamoDB for recent scans in this household
        response = history_table.query(
            KeyConditionExpression=Key('householdId').eq(principal_household),
            ScanIndexForward=False, # Attempt descending order if range key allows
            Limit=20
        )
        
        items = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"history": items})
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
