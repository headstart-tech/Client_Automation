""" This File Contains Test Cases for Updating a Super Account Manager """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_update_sam_unauthenticated(http_client_test):
    """ Test Case: Update Super Account Manager Without Authentication """
    response = await http_client_test.put(
        f"/super_account_manager/update/123456789012345678901234?feature_key={feature_key}",
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_update_sam_invalid_token(http_client_test):
    """ Test Case: Update Super Account Manager With Invalid Token """
    response = await http_client_test.put(
        f"/super_account_manager/update/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_update_sam_permission_denied(http_client_test, access_token):
    """ Test Case: Update Attempt By Unauthorized User (Student) """
    response = await http_client_test.put(
        f"/super_account_manager/update/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_update_sam_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Update Super Account Manager With Invalid ID Format """

    response = await http_client_test.put(
        f"/super_account_manager/update/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid Super Account Manager Id"}

@pytest.mark.asyncio
async def test_update_sam_not_found(http_client_test, super_admin_token):
    """ Test Case: Super Account Manager Not Found """
    fake_object_id = ObjectId()
    response = await http_client_test.put(
        f"/super_account_manager/update/{fake_object_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_sam_success(http_client_test, college_super_admin_access_token, test_get_super_account_manager):
    """ Test Case: Successfully Update Super Account Manager """
    response = await http_client_test.put(
        f"/super_account_manager/update/{str(test_get_super_account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"email": "updated_sam@exampler.com", "mobile_number": "8855446625"}
    )
    assert response.status_code == 200
    from app.database.configuration import DatabaseConfiguration
    updated_sam = await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(str(test_get_super_account_manager.get('_id'))), "user_type": "super_account_manager"})
    assert updated_sam.get("email") == "updated_sam@exampler.com"
    assert updated_sam.get("mobile_number") == "8855446625"
