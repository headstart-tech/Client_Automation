""" This file contains test cases for delete approval request which are in pending state """
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_request_no_authentication(setup_module, http_client_test):
    """
    Test delete request without authentication
    """
    from app.database.configuration import DatabaseConfiguration
    requests = await DatabaseConfiguration().approvals_collection.find({}).to_list(length=None)
    approval_id = str(requests[0].get("_id"))
    response = await http_client_test.delete(
        f"/approval/delete_request/{approval_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_delete_request_bad_credentials(setup_module, http_client_test):
    """
    Test delete request with bad credentials
    """
    from app.database.configuration import DatabaseConfiguration
    requests = await DatabaseConfiguration().approvals_collection.find({}).to_list(length=None)
    approval_id = str(requests[0].get("_id"))
    response = await http_client_test.delete(
        f"/approval/delete_request/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_delete_request_no_permission(setup_module, http_client_test, access_token):
    """
    Test delete request without permission
    """
    from app.database.configuration import DatabaseConfiguration
    requests = await DatabaseConfiguration().approvals_collection.find({}).to_list(length=None)
    approval_id = str(requests[0].get("_id"))
    response = await http_client_test.delete(
        f"/approval/delete_request/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_delete_request_invalid_approval_id(setup_module, http_client_test, college_super_admin_access_token):
    """
    Test delete request with invalid approval id
    """
    response = await http_client_test.delete(
        f"/approval/delete_request/123?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_request_approval_not_found(setup_module, http_client_test, college_super_admin_access_token):
    """
    Test delete request with invalid approval id
    """
    random_id = "60f1b9b3b3b3b3b3b3b3b3b3"
    response = await http_client_test.delete(
        f"/approval/delete_request/{random_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404



@pytest.mark.asyncio
async def test_delete_request(setup_module, http_client_test, college_super_admin_access_token):
    """
    Test delete request
    """
    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    requests = await DatabaseConfiguration().approvals_collection.find({}).to_list(length=None)
    approval_id = str(requests[0].get("_id"))
    response = await http_client_test.delete(
        f"/approval/delete_request/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Approval Request Deleted Successfully."

    requests = await DatabaseConfiguration().approvals_collection.find_one(
        {'_id': ObjectId(response.json().get("approval_id"))})
    assert requests is None