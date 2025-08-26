"""
This file contains test cases for get languages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_languages_not_authenticated(http_client_test, setup_module,
                                                   test_college_validation):
    """
    Not authenticate for get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_languages_bad_token(http_client_test, test_college_validation,
                                 setup_module, access_token):
    """
    bad token to get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_language_college_id(http_client_test, super_admin_access_token,
                                                     setup_module):
    """
    Required college_id for get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_languages_invalid_college_id(http_client_test, super_admin_access_token,
                                                             setup_module):
    """
    invalid  college_id for get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?college_id=1234&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'}

@pytest.mark.asyncio
async def test_get_languages_not_found_college_id(http_client_test, super_admin_access_token,
                                                             setup_module):
    """
    not found college_id for get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?college_id=123456789012345678901234"
                                          f"&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": 'College not found.'}

@pytest.mark.asyncio
async def test_get_languages_data_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                               setup_module, access_token):
    """
    Not permission for get languages
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/"
                                          f"?college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_languages(http_client_test, test_college_validation, college_counselor_access_token,
                                 setup_module,):
    """
    Get the details of leads_application data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_human_languages/?college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get languages"
