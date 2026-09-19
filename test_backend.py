import json
import sys
import os

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))
from scans.app import lambda_handler
import scans.app

class MockTable:
    def get_item(self, Key):
        if Key['profileId'] == 'prof_1':
            return {'Item': {
                'householdId': 'hh_1',
                'profileId': 'prof_1',
                'name': 'Test User',
                'age': 25,
                'weight_kg': 70.0,
                'height_cm': 175.0,
                'gender': 'male',
                'tracked_nutrients': ['Energy_kcal', 'Protein', 'Carbs', 'Sugars', 'Fat', 'Fiber']
            }}
        return {}
        
    def put_item(self, Item):
        pass

assert scans.app.default_limits["Energy_kcal"] == 2130.0

# Monkey-patch the tables in scans.app
scans.app.profiles_table = MockTable()
scans.app.history_table = MockTable()

def test_backend():
    print("Running backend evaluation for a scan...")
    event = {
        'httpMethod': 'POST',
        'path': '/api/evaluate',
        'body': json.dumps({
            'barcode': '5000159461122',
            'active_profile_ids': ['prof_1']
        })
    }
    
    response = lambda_handler(event, None)
    print("\n--- Backend Response ---")
    print(json.dumps(json.loads(response['body']), indent=2))

if __name__ == '__main__':
    test_backend()
