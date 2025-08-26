"""  This file contains test cases for create approval request """
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_approval_no_authentication(setup_module, http_client_test, new_approval_request_data):
    """
    Test create approval request without authentication
    """

    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_create_approval_bad_credentials(setup_module, http_client_test, new_approval_request_data):
    """
    Test create approval request with bad credentials
    """

    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data,
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_create_approval_no_permission(setup_module, http_client_test, new_approval_request_data, access_token):
    """
    Test create approval request without permission
    """

    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_create_approval_invalid_approval_type(setup_module, http_client_test, new_approval_request_data, college_super_admin_access_token):
    """
    Test create approval request
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().approvals_collection.delete_many({})
    new_approval_request_data["approval_type"] = "invalid_approval_type"
    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_approval(setup_module, http_client_test, new_approval_request_data, college_super_admin_access_token):
    """
    Test create approval request
    """
    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    await DatabaseConfiguration().approvals_collection.delete_many({})
    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Approval Request Created Successfully."

    requests = await DatabaseConfiguration().approvals_collection.find_one({'_id': ObjectId(response.json().get("approval_id"))})
    assert requests is not None