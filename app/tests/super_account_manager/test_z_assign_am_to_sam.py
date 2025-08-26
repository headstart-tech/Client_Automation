""" This File Contains Test Cases for Assigning Account Managers to Super Account Manager """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_assign_am_unauthenticated(http_client_test):
    """ Test Case: Assign Account Managers Without Authentication """
    response = await http_client_test.put(
        f"/super_account_manager/assign-account-managers/123456789012345678901234?feature_key={feature_key}",
        json={"account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_assign_am_invalid_token(http_client_test):
    """ Test Case: Assign Account Managers With Invalid Token """
    response = await http_client_test.put(
        f"/super_account_manager/assign-account-managers/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json={"account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_assign_am_permission_denied(http_client_test, access_token):
    """ Test Case: Assign Account Managers When User Has Insufficient Permissions """
    response = await http_client_test.put(
        f"/super_account_manager/assign-account-managers/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_assign_am_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Assign Account Managers With Invalid Super Account Manager Id Format """
    response = await http_client_test.put(
        f"/super_account_manager/assign-account-managers/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_assign_am_not_found(http_client_test, super_admin_token):
    """ Test Case: Super Account Manager Not Found """
    fake_object_id = ObjectId()  # Generate a fake ObjectId
    response = await http_client_test.put(
        f"/assign-account-managers/{fake_object_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json={"account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_am_success(http_client_test, college_super_admin_access_token, test_get_super_account_manager):
    """ Test Case: Successfully Assign Account Managers to Super Account Manager """
    # Assuming test_get_super_account_manager is a fixture returning a valid SAM document with field _id.
    from app.database.configuration import DatabaseConfiguration
    sam = await DatabaseConfiguration().user_collection.find_one(
        {"email": "raj.kumar@domain.in"}
    )
    super_account_manager_id = str(sam.get("_id"))
    am = await DatabaseConfiguration().user_collection.find_one(
        {"user_type": "account_manager"}
    )
    request_payload = {
        "account_manager_ids": [
            str(am.get("_id"))
        ]
    }
    response = await http_client_test.put(
        f"/super_account_manager/assign-account-managers/{super_account_manager_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=request_payload
    )
    assert response.status_code == 200

    # Validate that the database has been updated accordingly.
    updated_sam = await DatabaseConfiguration().user_collection.find_one(
        {"_id": ObjectId(super_account_manager_id), "user_type": "super_account_manager"}
    )
    # Assuming the assigned_account_managers field is updated with details containing account_manager_id.
    assigned_am_ids = [str(am.get("account_manager_id")) for am in updated_sam.get("assigned_account_managers", [])]
    # Check that the new account managers have been added
    for am_id in request_payload["account_manager_ids"]:
        assert am_id in assigned_am_ids