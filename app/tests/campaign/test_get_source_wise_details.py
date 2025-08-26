"""
This file contains test cases related to API route/endpoint get
 source wise details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_campaign_data_not_authenticated(http_client_test,
                                                   test_college_validation,
                                                   setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_wise_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_campaign_data_bad_credentials(http_client_test,
                                                 test_college_validation,
                                                 setup_module):
    """
    Bad token for get source wise details
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_wise_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_campaign_data_no_permission(
        http_client_test, test_college_validation, access_token,
        test_campaign_data, setup_module
):
    """
    No permission for get source wise details
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_wise_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_campaign_data(http_client_test, test_college_validation,
                                 college_super_admin_access_token,
                                 test_campaign_data, setup_module):
    """
    Get source wise details
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_wise_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get source wise details."


@pytest.mark.asyncio
async def test_get_campaign_source_wise_data_based_on_date_range(
        http_client_test, test_college_validation,
        college_super_admin_access_token,
        test_campaign_data, setup_module, start_end_date):
    """
    Get source wise details based on date range
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_wise_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date)
    assert response.status_code == 200
    assert response.json()['message'] == "Get source wise details."
