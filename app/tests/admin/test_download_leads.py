"""
This file contains test cases for download leads
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_download_leads_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_download_leads_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for download leads
    """
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_download_leads_no_permission(
        http_client_test, test_college_validation, super_admin_access_token, setup_module
):
    """
    No permission for download leads
    """
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_download_leads_required_college_id(http_client_test, test_college_validation,
                                                  college_super_admin_access_token):
    """
    Required college id for download leads
    """
    response = await http_client_test.post(f"/admin/all_leads/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_download_leads_invalid_college_id(http_client_test, test_college_validation,
                                                 college_super_admin_access_token):
    """
    Invalid college id for download leads
    """
    response = await http_client_test.post(f"/admin/all_leads/?college_id=1234567890&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_download_leads_college_not_found(http_client_test, test_college_validation,
                                                college_super_admin_access_token):
    """
    College not found for download leads
    """
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_download_leads_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    No found for download leads
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "No found."}


@pytest.mark.asyncio
async def test_download_leads(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_student_validation
):
    """
    Download leads
    """
    response = await http_client_test.post(
        f"/admin/download_leads/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"student_ids": [str(test_student_validation.get("_id"))]}
    )
    assert response.status_code == 200
    assert "file_url" in response.json()
    assert response.json()["message"] == "File downloaded successfully."
