"""
This file contains test cases related to API route/endpoint map data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_map_data_not_authenticated(
        http_client_test, setup_module, test_college_validation
):
    """
    Get map data
    """
    response = await http_client_test.post(f"/map_data/{str(test_college_validation.get('_id'))}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_map_data_college_not_found(
        http_client_test, setup_module, college_super_admin_access_token,
):
    """
    College not found for map data
    """
    response = await http_client_test.post(f"/map_data/123456789012345678901234?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 404
    assert response.json() == {"detail": "College not found. Make sure college id should be correct."}


@pytest.mark.asyncio
async def test_map_data_invalid_college_id(
        http_client_test, setup_module, college_super_admin_access_token
):
    """
    College not found for map data
    """
    response = await http_client_test.post(f"/map_data/1234567890?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string."}


@pytest.mark.asyncio
async def test_map_data_student_not_found(http_client_test, test_college_validation, college_super_admin_access_token):
    """
    Student not found for map data
    """
    response = await http_client_test.post(f"/map_data/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Data fetched successfully."


@pytest.mark.asyncio
async def test_map_data(http_client_test, test_college_validation, college_super_admin_access_token):
    """
    Get map data
    """
    response = await http_client_test.post(f"/map_data/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Data fetched successfully."


@pytest.mark.asyncio
async def test_map_data_by_season_wise(http_client_test, test_college_validation, college_super_admin_access_token,
                                       start_end_date):
    """
    Test case -> for map data season wise
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/map_data/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"season": 'test'})
    assert response.status_code == 200
    assert response.json()['message'] == "Data fetched successfully."


@pytest.mark.asyncio
async def test_map_data_by_season_wise_no_found(http_client_test, test_college_validation,
                                                college_super_admin_access_token):
    """
    No found for map data season wise
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.delete_many({})
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    response = await http_client_test.post(
        f"/map_data/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()['message'] == "Data fetched successfully."
    assert response.json()['data'][0]['total_applications'] == 0
