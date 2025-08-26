"""
This file contains test cases related to automation list details
 API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_automation_list_details_not_authenticated(
        http_client_test, setup_module,
        test_college_validation,):
    """
    Not authenticated test case
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_automation_list_details_bad_credentials(
        http_client_test,
        test_college_validation,
        setup_module):
    """
    Bad credentials to get automation list
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_automation_list_details_college_id_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id required to get automation list details
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_automation_list_details_college_id_not_found(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id not found to get automation list details
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_automation_list_details_college_id_invalid(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id invalid to get automation list
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list"
        f"?college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_automation_list_details_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    No permission to get automation top bar data
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_automation_list_details(
        http_client_test, college_super_admin_access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper):
    """
    Test case to get automations top bar
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_list"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Automation List Details."
