"""
This file contains test cases related to API route/endpoint for get school names
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_school_names(
        http_client_test, access_token, test_college_validation,
        college_super_admin_access_token, setup_module, test_course_validation
):
    """
    Different test cases scenarios for get school names
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated - when user not logged in
    response = await http_client_test.get(
        f"/admin/school_names/?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad/wrong token send in the request header for get school names
    response = await http_client_test.get(f"/admin/school_names/?college_id={college_id}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # User don't have permission for get school names
    response = await http_client_test.get(
        f"/admin/school_names/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Required college id for get school names
    response = await http_client_test.get(f"/admin/school_names/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for get school names
    response = await http_client_test.get(
        f"/admin/school_names/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found for get school names
    response = await http_client_test.get(
        f"/admin/school_names/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Get school names
    response = await http_client_test.get(
        f"/admin/school_names/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['data'] is not None
    assert response.json()['message'] == "Get school names"

    # School names not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().course_collection.delete_many({})
    response = await http_client_test.get(
        f"/admin/school_names/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['data'] == {}
    assert response.json()['message'] == "Get school names"
