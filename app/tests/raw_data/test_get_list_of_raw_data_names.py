"""
This file contains test cases for get list of raw data names
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_list_of_raw_data_names_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/manage/list_of_raw_data_names/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_list_of_raw_data_names_wrong_token(http_client_test, test_college_validation, setup_module,
                                                  access_token):
    """
    Wrong token for get list of raw data names
    """
    response = await http_client_test.get(
        f"/manage/list_of_raw_data_names/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_list_of_raw_data_names_no_permission(http_client_test, test_college_validation, access_token,
                                                    setup_module):
    """
    No permission for get list of raw data names
    """
    response = await http_client_test.get(
        f"/manage/list_of_raw_data_names/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_list_of_raw_data_names(http_client_test, test_college_validation, college_super_admin_access_token,
                                      setup_module,
                                      test_offline_data_validation):
    """
    Get list of raw data names
    """
    response = await http_client_test.get(
        f"/manage/list_of_raw_data_names/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == 'Get list of raw data names.'


@pytest.mark.asyncio
async def test_list_of_raw_data_names_no_found(http_client_test, test_college_validation,
                                               college_super_admin_access_token, setup_module):
    """
    Get list of raw data names
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().offline_data.delete_many({})
    response = await http_client_test.get(
        f"/manage/list_of_raw_data_names/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == 'Get list of raw data names.'
    assert response.json()["data"] == []
