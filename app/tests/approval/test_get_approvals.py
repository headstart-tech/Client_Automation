""" This file contains test cases for Getting Approval Request which were created by user """

import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_requests_no_authentication(setup_module, http_client_test):
    """
    Test create approval request without authentication
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_requests_bad_credentials(setup_module, http_client_test):
    """
    Test create approval request with bad credentials
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_requests_no_permission(setup_module, http_client_test, access_token):
    """
    Test create approval request without permission
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_requests(setup_module, http_client_test, college_super_admin_access_token):
    """
    Test create approval request without permission
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_requests_no_authentication(setup_module, http_client_test):
    """
    Test create approval request without authentication
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_requests_bad_credentials(setup_module, http_client_test):
    """
    Test create approval request with bad credentials
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_requests_no_permission(setup_module, http_client_test, access_token):
    """
    Test create approval request without permission
    """

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_requests(setup_module, http_client_test, college_super_admin_access_token, new_approval_request_data):
    """
    Test create approval request without permission
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().approvals_collection.delete_many({})
    response = await http_client_test.post(
        f"/approval/create_request?feature_key={feature_key}",
        json=new_approval_request_data,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Approval Request Created Successfully."

    response = await http_client_test.get(
        f"/approval/get_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200



# Test Case: Get All Approval Requests Without Authentication
@pytest.mark.asyncio
async def test_get_all_approval_requests_unauthenticated(http_client_test):
    """ Test Case: Get All Approval Requests Without Authentication """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Get All Approval Requests With Invalid Token
@pytest.mark.asyncio
async def test_get_all_approval_requests_invalid_token(http_client_test):
    """ Test Case: Get All Approval Requests With Invalid Token """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Get All Approval Requests Without Permission
@pytest.mark.asyncio
async def test_get_all_approval_requests_no_permission(http_client_test, access_token):
    """ Test Case: Get All Approval Requests Without Permission """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Get All Approval Requests With Invalid Approval Type Filter
@pytest.mark.asyncio
async def test_get_all_approval_requests_invalid_type(http_client_test, college_super_admin_access_token):
    """ Test Case: Get All Approval Requests With Invalid Approval Type Filter """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"approval_type": ["invalid_type"], "approval_status": []}
    )
    assert response.status_code == 422
    assert "Invalid Approval Type" in response.json()["detail"]


# Test Case: Get All Approval Requests With Invalid Approval Status Filter
@pytest.mark.asyncio
async def test_get_all_approval_requests_invalid_status(http_client_test, college_super_admin_access_token):
    """ Test Case: Get All Approval Requests With Invalid Approval Status Filter """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"approval_type": [], "approval_status": ["invalid_status"]}
    )
    assert response.status_code == 422
    assert "Invalid Approval Status" in response.json()["detail"]


# Test Case: Get All Approval Requests Success Without Pagination
@pytest.mark.asyncio
async def test_get_all_approval_requests_success_no_pagination(http_client_test, college_super_admin_access_token):
    """ Test Case: Get All Approval Requests Success Without Pagination """
    response = await http_client_test.post(
        f"/approval/get_all_approval_requests?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"approval_type": [], "approval_status": []}
    )
    assert response.status_code == 200


# Test Case: Get Request Data Without Authentication
@pytest.mark.asyncio
async def test_get_request_data_unauthenticated(http_client_test):
    """ Test Case: Get Request Data Without Authentication """
    approver_id = "507f1f77bcf86cd799439011"
    response = await http_client_test.get(f"/approval/get_request_data/{approver_id}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Get Request Data With Invalid Token
@pytest.mark.asyncio
async def test_get_request_data_invalid_token(http_client_test):
    """ Test Case: Get Request Data With Invalid Token """
    approver_id = "507f1f77bcf86cd799439011"
    response = await http_client_test.get(
        f"/approval/get_request_data/{approver_id}?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Get Request Data When User Lacks Permission
@pytest.mark.asyncio
async def test_get_request_data_permission_denied(http_client_test, access_token):
    """ Test Case: Get Request Data When User Lacks Permission """
    approver_id = str(ObjectId())
    response = await http_client_test.get(
        f"/approval/get_request_data/{approver_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Get Request Data With Invalid Id Format
@pytest.mark.asyncio
async def test_get_request_data_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Get Request Data With Invalid Id Format """
    response = await http_client_test.get(
        f"/approval/get_request_data/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422


# Test Case: Approval Request Data Not Found
@pytest.mark.asyncio
async def test_get_request_data_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Approval Request Data Not Found """
    approver_id = str(ObjectId())
    response = await http_client_test.get(
        f"/approval/get_request_data/{approver_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404


# Test Case: Successfully Get Approval Request Data
@pytest.mark.asyncio
async def test_get_request_data_success(http_client_test, college_super_admin_access_token):
    """ Test Case: Successfully Get Approval Request Data """
    from app.database.configuration import DatabaseConfiguration
    approval = await DatabaseConfiguration().approvals_collection.find_one()
    approver_id = str(approval.get("_id"))
    response = await http_client_test.get(
        f"/approval/get_request_data/{approver_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200