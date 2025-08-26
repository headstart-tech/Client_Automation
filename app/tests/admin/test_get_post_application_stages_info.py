"""
This file contains test cases related to API route/endpoint for get post
application stages info
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_post_application_stages_info_authentication(
        http_client_test, test_college_validation, setup_module):
    """
    Check authentication send wrong token
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_post_application_stages_info_required_application_id(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, application_details
):
    """
    No permission for get post application stages info
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be required and ' \
                                        'valid.'


@pytest.mark.asyncio
async def test_get_post_application_stages_info_required_college_id(
        http_client_test, test_college_validation,
        college_super_admin_access_token):
    """
    Required college id for get post application stages info
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'


@pytest.mark.asyncio
async def test_get_post_application_stages_info_invalid_college_id(
        http_client_test, test_college_validation,
        college_super_admin_access_token):
    """
    Invalid college id for get post application stages info
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_post_application_stages_info_college_not_found(
        http_client_test, test_college_validation,
        college_super_admin_access_token):
    """
    College not found for get post application stages info
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_post_application_stages_info(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, application_details
):
    """
    No permission for get post application stages info
    """
    response = await http_client_test.get(
        f"/admin/post_application_stages_info/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 200
    for name in ["document_verification", "application_selection",
                 "interview", "offer_letter_release"]:
        assert name in response.json()
