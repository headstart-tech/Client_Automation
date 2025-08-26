"""
This file contains test cases related to get course details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_course_details_required_college_id(http_client_test, college_super_admin_access_token,
                                                      test_college_data, setup_module, test_college_validation):
    """
    Required college id for get course details
    """
    response = await http_client_test.get(f"/college/get_course_details/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and valid."


@pytest.mark.asyncio
async def test_get_course_details(http_client_test, setup_module, test_college_validation):
    """
    Get course details
    """
    response = await http_client_test.get(
        f"/college/get_course_details/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json()['message'] == "Get all course details."


@pytest.mark.asyncio
async def test_get_course_details_by_name(http_client_test, setup_module, test_college_validation):
    """
    Get course details
    """
    response = await http_client_test.get(
        f"/college/get_course_details/?college_id={str(test_college_validation.get('_id'))}&course_name=BSc")
    assert response.status_code == 200
    assert response.json()['message'] == "Get course details."
