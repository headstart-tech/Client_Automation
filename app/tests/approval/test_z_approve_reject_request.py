""" This File Contains Test Cases for Updating Approval Request Status """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Test Case: Update Status Without Authentication
@pytest.mark.asyncio
async def test_update_status_unauthenticated(setup_module, http_client_test):
    """ Test Case: Update Status Without Authentication """
    response = await http_client_test.put(
        f"/approval/update_status/123456789012345678901234?feature_key={feature_key}",
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# Test Case: Update Status With Invalid Token
@pytest.mark.asyncio
async def test_update_status_invalid_token(http_client_test):
    """ Test Case: Update Status With Invalid Token """
    response = await http_client_test.put(
        f"/approval/update_status/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test case with No Permission
@pytest.mark.asyncio
async def test_update_status_no_permission(http_client_test, access_token):
    """ Test Case: Update Status Without Permission """
    response = await http_client_test.put(
        f"/approval/update_status/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Update Status With Invalid status Query Param
@pytest.mark.asyncio
async def test_update_status_invalid_status_param(http_client_test, college_super_admin_access_token):
    """ Test Case: Update Status With Invalid status Query Param """
    response = await http_client_test.put(
        f"/approval/update_status/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "invalid"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 400


# Test Case: Update Status With Invalid Approval Id
@pytest.mark.asyncio
async def test_update_status_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Update Status With Invalid Approval Id """
    response = await http_client_test.put(
        f"/approval/update_status/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "reject"},
        json={"remarks": "No longer needed"}
    )
    assert response.status_code == 422


# Test Case: Approval Request Not Found
@pytest.mark.asyncio
async def test_update_status_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Approval Request Not Found """
    response = await http_client_test.put(
        f"/approval/update_status/{str(ObjectId())}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Proceed"}
    )
    assert response.status_code == 404


# Test Case: Successfully Reject Approval Request
@pytest.mark.asyncio
async def test_update_status_reject_success(http_client_test, college_super_admin_access_token, test_client_automation_college_id):
    """ Test Case: Successfully Reject Approval Request """
    college_id = str(test_client_automation_college_id)
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "reject"},
        json={"remarks": "Not applicable"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Approval Request Rejected Successfully."}


# Test Case: Approval Request Already Processed
@pytest.mark.asyncio
async def test_update_status_reject_already_processed(http_client_test, college_super_admin_access_token):
    """ Test Case: Approval Request Already Processed """
    from app.database.configuration import DatabaseConfiguration
    approvals = await DatabaseConfiguration().approvals_collection.find_one({"status": "rejected"})
    response = await http_client_test.put(
        f"/approval/update_status/{str(approvals['_id'])}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "reject"},
        json={"remarks": "Not applicable"}
    )
    assert response.status_code == 422


# Test Case: Successfully Approve Approval Request
@pytest.mark.asyncio
async def test_update_status_approve_success(http_client_test, test_client_automation_college_id,
                                             college_super_admin_access_token, new_approval_request_data):
    """ Test Case: Successfully Approve Approval Request """
    # Creating a New Approval
    college_id = str(test_client_automation_college_id)
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 200
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "reject"},
        json={"remarks": "Not good"}
    )
    assert response.status_code == 200