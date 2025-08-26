"""
This file contains test cases to delete automation
 API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_automation_not_authenticated(
        http_client_test, setup_module,
        test_college_validation,):
    """
    Not authenticated test case
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_automation_bad_credentials(
        http_client_test,
        test_college_validation,
        setup_module):
    """
    Bad credentials to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_automation_college_id_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id required to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_delete_automation_college_id_not_found(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id not found to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_delete_automation_college_id_invalid(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    College id invalid to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation"
        f"?college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_delete_automation_no_permission(
        http_client_test, access_token, setup_module, test_college_validation, test_automation_validation
):
    """
    No permission to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_automation_validation.get("_id"))],
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_automation(
        http_client_test, college_super_admin_access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper):
    """
    Test case to delete automation
    """
    response = await http_client_test.post(
        f"/nested_automation/delete_automation"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_automation_validation.get("_id"))],
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Automations which are not active are deleted successfully!"
