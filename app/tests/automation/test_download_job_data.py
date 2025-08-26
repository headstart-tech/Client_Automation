"""
This file contains test cases related to download job data API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo: We are delete this route first confirmation
@pytest.mark.asyncio
async def test_download_job_data_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/automation/download_job_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_download_job_data_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for download job data
    """
    response = await http_client_test.post(
        f"/automation/download_job_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_download_job_data_required_automation_job_id(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required automation job id for download job data
    """
    response = await http_client_test.post(
        f"/automation/download_job_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Automation Job Id must be required and valid.'}


@pytest.mark.asyncio
async def test_download_job_data_no_permission(
        http_client_test, test_college_validation, access_token, test_automation_rule_details_validation, setup_module
):
    """
    No permission for download job data
    """
    response = await http_client_test.post(
        f"/automation/download_job_data/?automation_job_id={test_automation_rule_details_validation}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_download_job_data(http_client_test, test_college_validation, college_super_admin_access_token,
                                 test_automation_rule_details_validation,
                                 setup_module):
    """
    For download job data
    """
    response = await http_client_test.post(
        f"/automation/download_job_data/?automation_job_id={test_automation_rule_details_validation}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "File downloaded successfully."


@pytest.mark.asyncio
async def test_download_job_data_no_found(http_client_test, test_college_validation, college_super_admin_access_token,
                                          test_automation_rule_details_validation,
                                          setup_module):
    """
    Download job data not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().automation_activity_collection.delete_many({})
    response = await http_client_test.post(
        f"/automation/download_job_data/?automation_job_id={test_automation_rule_details_validation}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Automation job not found. Make sure automation job id is correct."}
