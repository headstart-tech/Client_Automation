"""
This file contains test cases related to API route/endpoint get counselor wise call data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get campaign data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_required_page_number(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for get campaign data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Page Num must be required and valid.'}
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page size for get campaign data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Page Size must be required and valid.'}
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    No permission for get campaign data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Not enough permissions'}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data(http_client_test, test_college_validation, college_super_admin_access_token,
                                            setup_module):
    """
    Get counselor wise call activity data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get counselor wise call activity data."


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_by_wrong_college_id(http_client_test, college_super_admin_access_token,
                                                                setup_module):
    """
    Get counselor wise call activity data by wrong college id
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id=12345678901234&page_num=1&"
        f"page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_college_not_found(http_client_test, college_super_admin_access_token,
                                                              setup_module):
    """
    College not found for get counselor wise call activity data
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id=123456789012345678901234&page_num=1"
        f"&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_based_on_date_range(http_client_test, test_college_validation,
                                                                college_super_admin_access_token, setup_module,
                                                                start_end_date):
    """
    Get counselor wise call activity data based on date range
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date)
    assert response.status_code == 200
    assert response.json()['message'] == "Get counselor wise call activity data."


@pytest.mark.asyncio
async def test_get_counselor_wise_call_data_based_by_wrong_date_range(http_client_test, test_college_validation,
                                                                      college_super_admin_access_token, setup_module,
                                                                      start_end_date):
    """
    Get counselor wise call activity data by wrong date range
    """
    response = await http_client_test.post(
        f"/call_activities/counselor_wise_data/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "start_date": "1998-01-01",
            "end_date": "1998-04-01"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get counselor wise call activity data."
    assert response.json()['data'] == []
