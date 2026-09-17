import json
import cedarpolicy

def check_permission(principal_id, principal_role, principal_household, action_name, resource_id, resource_owner, resource_household):
    """
    Evaluates a Cedar policy to check if the principal has permission to perform the action on the resource.
    """
    
    # In a real AWS environment with AVP, we would use boto3.client('verifiedpermissions').is_authorized().
    # For SAM Local/offline demo, we use the local cedarpolicy python binding.
    
    entities = [
        {
            "uid": {"type": "AaharKavach::User", "id": principal_id},
            "attrs": {
                "role": principal_role,
                "householdId": principal_household
            },
            "parents": []
        },
        {
            "uid": {"type": "AaharKavach::Profile", "id": resource_id},
            "attrs": {
                "owner": {"type": "AaharKavach::User", "id": resource_owner},
                "householdId": resource_household
            },
            "parents": []
        }
    ]
    
    request = {
        "principal": f'AaharKavach::User::"{principal_id}"',
        "action": f'AaharKavach::Action::"{action_name}"',
        "resource": f'AaharKavach::Profile::"{resource_id}"',
        "context": {}
    }

    try:
        with open('../policies/policies.cedar', 'r') as f:
            policies_str = f.read()
        
        # Note: cedarpolicy interface might vary depending on version. This is typical for python bindings.
        # Evaluation
        is_authorized = cedarpolicy.is_authorized(request, policies_str, json.dumps(entities))
        return is_authorized.decision == "Allow"
    except Exception as e:
        print(f"Cedar Evaluation Error: {e}")
        return False
