""" This File Contains Test Cases Related to Getting Super Account Manager """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_sam_no_authentication(http_client_test, setup_module):
    """ Test Case: Get Super Account Manager Without Authentication """
    sam_id = str(ObjectId())
    response = await http_client_test.get(f"/super_account_manager/get/{sam_id}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_sam_bad_token(http_client_test, setup_module):
    """ Test Case: Get Super Account Manager With Invalid Token """
    sam_id = str(ObjectId())
    response = await http_client_test.get(
        f"/super_account_manager/get/{sam_id}?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_sam_no_permission(http_client_test, setup_module, access_token, test_get_super_account_manager):
    """ Test Case: Super Account Manager Accessing Another's Data (Permission Denied) """
    response = await http_client_test.get(
        f"/super_account_manager/get/{str(test_get_super_account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_sam_invalid_id(http_client_test, setup_module, college_super_admin_access_token):
    """ Test Case: Get Super Account Manager With Invalid ID Format """
    invalid_id = "123-invalid-id"
    response = await http_client_test.get(
        f"/super_account_manager/get/{invalid_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid Super Account Manager Id"}

@pytest.mark.asyncio
async def test_get_sam_not_found(http_client_test, setup_module, college_super_admin_access_token):
    """ Test Case: Get Super Account Manager With Valid But Non-existent ID """
    non_existing_id = str(ObjectId())
    response = await http_client_test.get(
        f"/super_account_manager/get/{non_existing_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_sam_success(http_client_test, setup_module, college_super_admin_access_token, test_get_super_account_manager):
    """ Test Case: Super Account Manager Accessing Their Own Data """
    response = await http_client_test.get(
        f"/super_account_manager/get/{str(test_get_super_account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result.get("_id") == str(test_get_super_account_manager.get('_id'))
    assert result.get("user_type") == "super_account_manager"
    assert "password" not in result

@pytest.mark.asyncio
async def test_get_all_sam_no_authentication(http_client_test, setup_module):
    """ Test Case: Get All Super Account Managers Without Authentication """
    response = await http_client_test.get(f"/super_account_manager/get_all?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_all_sam_invalid_token(http_client_test, setup_module):
    """ Test Case: Get All Super Account Managers With Invalid Token """
    response = await http_client_test.get(
        f"/super_account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": "Bearer fake_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_all_sam_no_permission(http_client_test, setup_module, access_token):
    """ Test Case: User Without Required Permissions (e.g. Student) Tries To Access """
    response = await http_client_test.get(
        f"/super_account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_all_sam_success(http_client_test, setup_module, college_super_admin_access_token):
    """ Test Case: Successfully Get All Super Account Managers (Without Pagination) """
    response = await http_client_test.get(
        f"/super_account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Super Account Manager Data List Found"
    assert isinstance(data["super_account_managers"], list)

@pytest.mark.asyncio
async def test_get_all_sam_with_pagination(http_client_test, setup_module, college_super_admin_access_token):
    """ Test Case: Get All Super Account Managers With Pagination """
    response = await http_client_test.get(
        f"/super_account_manager/get_all?page=1&limit=2&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Super Account Manager Data List Found"
    assert isinstance(data.get("data", []), list)