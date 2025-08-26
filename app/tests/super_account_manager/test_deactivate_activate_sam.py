""" This file contains test cases related to deactivate and activate super account manager """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_deactivate_sam_unauthenticated(http_client_test):
    """ Test Case: Deactivate Super Account Manager Without Authentication """
    response = await http_client_test.put(
        f"/super_account_manager/deactivate/123456789012345678901234?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_deactivate_sam_invalid_token(http_client_test):
    """ Test Case: Deactivate Super Account Manager With Invalid Token """
    response = await http_client_test.put(
        f"/super_account_manager/deactivate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_deactivate_sam_permission_denied(http_client_test, access_token):
    """ Test Case: Deactivation Attempt By Unauthorized User (Student) """
    response = await http_client_test.put(
        f"/super_account_manager/deactivate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_deactivate_sam_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Deactivate Super Account Manager With Invalid ID Format """

    response = await http_client_test.put(
        f"/super_account_manager/deactivate/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid Super Account Manager Id"}

@pytest.mark.asyncio
async def test_deactivate_sam_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Super Account Manager Not Found """
    new_id = ObjectId()

    response = await http_client_test.put(
        f"/super_account_manager/deactivate/{new_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_deactivate_sam_has_allocated_account_managers(http_client_test, college_super_admin_access_token):
    """ Test Case: Deactivate SAM With Allocated Account Managers """

    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one({"user_type": "account_manager"})
    sam_id = account_manager.get("associated_super_account_manager")

    response = await http_client_test.put(
        f"/super_account_manager/deactivate/{str(sam_id)}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Super Account Manager have Allocated Account Managers"}

@pytest.mark.asyncio
async def test_deactivate_sam_success(http_client_test, super_admin_token, test_get_account_manager):
    """ Test Case: Successfully Deactivate Super Account Manager """
    from app.database.configuration import DatabaseConfiguration
    sam = await DatabaseConfiguration().user_collection.find_one(
        {"email": "raj.kumar@domain.in"}
    )
    response = await http_client_test.put(
        f"/super_account_manager/deactivate/{str(sam.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Super Account Manager Deactivated Successfully"

@pytest.mark.asyncio
async def test_deactivate_sam_already_deactivated(http_client_test, super_admin_token, test_get_account_manager):
    """ Test Case: Already Deactivated Super Account Manager """
    from app.database.configuration import DatabaseConfiguration
    sam = await DatabaseConfiguration().user_collection.find_one(
        {"email": "raj.kumar@domain.in"}
    )
    response = await http_client_test.put(
        f"/super_account_manager/deactivate/{str(sam.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Super Account Manager Already Deactivated"}

@pytest.mark.asyncio
async def test_activate_sam_unauthenticated(http_client_test):
    """ Test Case: Activate Super Account Manager Without Authentication """
    response = await http_client_test.put(
        f"/super_account_manager/activate/123456789012345678901234?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_activate_sam_invalid_token(http_client_test):
    """ Test Case: Activate Super Account Manager With Invalid Token """
    response = await http_client_test.put(
        f"/super_account_manager/activate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_activate_sam_permission_denied(http_client_test, access_token):
    """ Test Case: Activation Attempt By Unauthorized User (Student) """
    response = await http_client_test.put(
        f"/super_account_manager/activate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_activate_sam_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Activate Super Account Manager With Invalid ID Format """
    response = await http_client_test.put(
        f"/super_account_manager/activate/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid Super Account Manager Id"}

@pytest.mark.asyncio
async def test_activate_sam_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Super Account Manager Not Found """
    response = await http_client_test.put(
        f"/super_account_manager/activate/{ObjectId()}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_activate_sam_success(http_client_test, college_super_admin_access_token):
    """ Test Case: Successfully Activate Super Account Manager """
    from app.database.configuration import DatabaseConfiguration
    sam = await DatabaseConfiguration().user_collection.find_one(
        {"email": "raj.kumar@domain.in"}
    )
    response = await http_client_test.put(
        f"/super_account_manager/activate/{str(sam.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Super Account Manager Activated Successfully"

@pytest.mark.asyncio
async def test_activate_sam_already_active(monkeypatch, http_client_test, college_super_admin_access_token):
    """ Test Case: Super Account Manager Already Activated """
    from app.database.configuration import DatabaseConfiguration
    sam = await DatabaseConfiguration().user_collection.find_one(
        {"email": "raj.kumar@domain.in"}
    )
    response = await http_client_test.put(
        f"/super_account_manager/activate/{str(sam.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Super Account Manager Already Activated"}