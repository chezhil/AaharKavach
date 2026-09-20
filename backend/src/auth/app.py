import json
import os
import uuid
import datetime
import bcrypt
import jwt
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.lambda_adapter import respond, json_body, run
from shared.contracts import Profile
from shared.store import save_profile, _use_dynamo

# In production, this should be stored in AWS Secrets Manager or KMS
JWT_SECRET = os.environ.get("JWT_SECRET", "super_secret_dev_key")

def signup_endpoint(body: dict) -> tuple[int, dict]:
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        return 400, {"error": "Username and password are required"}

    # Generate IDs
    household_id = f"hh_{uuid.uuid4().hex[:8]}"
    profile_id = f"prof_{uuid.uuid4().hex[:8]}"

    # Hash Password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Note: In a full app, we'd have a separate 'Accounts' table for logins. 
    # For AaharKavach hackathon, we simulate this by storing auth data in the 
    # Profile or relying purely on the generated JWT for subsequent requests.
    # We will create the Profile record as the Household ADMIN.

    age = int(body.get("age", 30)) if body.get("age") else None
    weight_kg = float(body.get("weight_kg", 70.0)) if body.get("weight_kg") else None
    height_cm = float(body.get("height_cm", 170.0)) if body.get("height_cm") else None
    gender = body.get("gender")
    allergies = body.get("allergies", [])
    
    # Tracked nutrients default
    tracked = ["Energy_kcal", "Protein", "Carbs", "Sugars", "Fat", "Salt"]

    # In contracts.py, allergies are mapped via restrictions. 
    # The actual implementation of saving the profile.
    # To keep it simple, we use a basic dict if store is raw dynamo, 
    # or rely on the Profile dataclass if it maps properly.
    
    profile = Profile(
        id=profile_id,
        name=username,
        household_role="ADMIN",
        restrictions=[], # We'll skip complex Restriction objects for now or add them if needed
        age=age,
        weight_kg=weight_kg,
        height_cm=height_cm,
        gender=gender,
        tracked_nutrients=tracked
    )
    
    # Manually save to dynamo to attach auth info (hackathon shortcut)
    if _use_dynamo():
        import boto3
        table = boto3.resource("dynamodb").Table(os.environ["PROFILES_TABLE"])
        item = profile.to_dict()
        item["householdId"] = household_id
        item["profileId"] = profile.id
        item["password_hash"] = hashed_password
        # Minimal allergen storage
        item["allergies_raw"] = allergies 
        table.put_item(Item=item)
    else:
        # Fallback local store logic
        pass

    # Generate JWT
    token_payload = {
        "sub": username,
        "householdId": household_id,
        "profileId": profile_id,
        "role": "ADMIN",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")

    return 201, {
        "token": token,
        "householdId": household_id,
        "profile": profile.to_dict()
    }

def lambda_handler(event, context):
    method = (event.get("httpMethod") or "POST").upper()
    path = event.get("path", "")
    
    if method == "OPTIONS":
        return respond(204, None)

    if method == "POST" and "signup" in path:
        return run(lambda: signup_endpoint(json_body(event)))

    return respond(405, {"error": "Method not allowed"})
