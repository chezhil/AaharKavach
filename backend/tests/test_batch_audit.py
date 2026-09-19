import pytest
from src.shared.api import audit_batch_endpoint, ApiError, Caller
from src.shared import store

# Dummy caller with a household ID
mock_caller = Caller(headers={"x-aahar-household": "hh_test_runner"})


def test_batch_audit_empty_barcodes():
    with pytest.raises(ApiError) as exc_info:
        audit_batch_endpoint(mock_caller, {"barcodes": []})
    assert exc_info.value.status == 400

def test_batch_audit_missing_household():
    caller_no_hh = Caller(headers={"x-aahar-household": ""})
    with pytest.raises(ApiError) as exc_info:
        audit_batch_endpoint(caller_no_hh, {"barcodes": ["123"]})
    assert exc_info.value.status == 400

def test_batch_audit_mixed_barcodes():
    # 5000159461122 is Cadbury (Dairy)
    # 8901058851304 is Maggi (Gluten, but maybe not dairy?)
    # 9999999999999 is Unknown
    body = {
        "barcodes": ["5000159461122", "8901058851304", "9999999999999"]
    }
    status, response = audit_batch_endpoint(mock_caller, body)
    
    assert status == 200
    assert "summary" in response
    assert response["summary"]["total_items"] == 3
    assert len(response["items"]) == 3
    
    unknown_item = next(i for i in response["items"] if i["status"] == "UNKNOWN")
    assert unknown_item["barcode"] == "9999999999999"
    
    known_items = [i for i in response["items"] if i["status"] == "KNOWN"]
    assert len(known_items) == 2
    
    cadbury = next(i for i in known_items if i["barcode"] == "5000159461122")
    assert cadbury["household_cleared"] is False
