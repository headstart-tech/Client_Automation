"""
This file contains test cases related to API route/endpoint get automation job details by id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo: We are delete this route first confirmation
@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_id_not_authenticated(http_client_test, test_college_validation,
                                                                           setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_id_bad_credentials(http_client_test, test_college_validation,
                                                                         setup_module):
    """
    Bad token for get automation job details by id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_invalid_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, access_token
):
    """
    Field required for get automation job details by id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Automation Job Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_id_no_permission(
        http_client_test, test_college_validation, access_token, test_automation_rule_details_validation, setup_module
):
    """
    No permission for get automation job details by id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?automation_job_id={test_automation_rule_details_validation}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_id(http_client_test, test_college_validation,
                                                         college_super_admin_access_token,
                                                         test_automation_rule_details_validation, setup_module):
    """
    Get automation job details by id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?automation_job_id={test_automation_rule_details_validation}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get automation job delivery details."


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_id_no_found(http_client_test, test_college_validation,
                                                                  college_super_admin_access_token,
                                                                  setup_module, test_automation_data):
    """
    Automation job not found by id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?automation_job_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Automation job not found. Make sure automation job id is correct."}


@pytest.mark.asyncio
async def test_get_automation_job_delivery_details_by_wrong_id(http_client_test, test_college_validation,
                                                               college_super_admin_access_token,
                                                               setup_module, test_automation_data):
    """
    Wrong automation job id
    """
    response = await http_client_test.get(
        f"/automation/job_delivery_details_by_id/?automation_job_id=1234567890123456789012"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Automation job id must be a 12-byte input or a 24-character hex string"}
