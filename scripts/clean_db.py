import json

with open("backend/.local-db.json", "r") as f:
    db = json.load(f)

# Keep only intended profiles in hh_1
db["profiles"] = [
    p for p in db.get("profiles", [])
    if p.get("householdId") != "hh_1" or not p.get("name", "").startswith("Test")
]

# Keep only valid scans (we can keep history for hh_1 if they are not automated test scans,
# but the tests used hh_1 and default users or maybe just random scans.
# Let's remove any scan history for "hh_test_runner" and any scans from hh_1 that were automated.
# Wait, automated scans were for Maggi, Parle-G, Snickers, Nutella, Coca-Cola.
# We can just remove scans from today that were automated, or just wipe history for demo?
# Prompt says: "Clear test entries from the recent scans database / local history storage so only genuine scans appear in the "RECENT SCANS" feed."
# Let's look at the history in db["history"].
# If we just keep a few known scans or just wipe history?
db["history"] = [
    h for h in db.get("history", [])
    if h.get("householdId") != "hh_test_runner" and "test_" not in h.get("userId", "")
]

# Actually, the automated scripts used X-Aahar-User: "test_user" or "user_test".
# Let's see what users were in the automated script.
# test_diverse_barcodes used X-Aahar-Household: "hh_test", X-Aahar-User: "user_test".
# Scripts previously used hh_1. Let's filter history where userId == "test_user" or "user_test".
db["history"] = [
    h for h in db.get("history", [])
    if h.get("userId") not in ["test_user", "user_test", ""]
]

with open("backend/.local-db.json", "w") as f:
    json.dump(db, f, indent=2)

print("Cleaned .local-db.json")
