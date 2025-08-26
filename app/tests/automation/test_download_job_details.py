"""
This file contains test cases related to download job details API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo: We are delete this route first confirmation
@pytest.mark.asyncio
async def test_download_job_details_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/automation/download_job_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_download_job_details_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for download job details
    """
    response = await http_client_test.post(
        f"/automation/download_job_details/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_download_job_details_no_permission(
        http_client_test, test_college_validation, access_token, test_automation_data, setup_module
):
    """
    No permission for download job details
    """
    response = await http_client_test.post(
        f"/automation/download_job_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_download_job_details(http_client_test, test_college_validation, college_super_admin_access_token,
                                    test_automation_rule_details_validation,
                                    setup_module):
    """
    For download job details
    """
    response = await http_client_test.post(
        f"/automation/download_job_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "File downloaded successfully."


@pytest.mark.asyncio
async def test_download_job_details_no_found(http_client_test, test_college_validation,
                                             college_super_admin_access_token, test_automation_data,
                                             setup_module):
    """
    Download job details not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().automation_activity_collection.delete_many({})
    response = await http_client_test.post(
        f"/automation/download_job_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == "Data not found."
