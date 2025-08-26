"""
This file contains test cases regarding for search_for_data_segment
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_search_for_data_segment_not_authenticated(
        http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in search_for_data_segment
    """
    response = await http_client_test.post(
        f"/data_segment/search_for_add_data_segment"
        f"?data_type=raw%20data&page_num=1&page_size=20"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_search_for_data_segment_bad_credentials(http_client_test,
                                                       test_college_validation,
                                                       setup_module):
    """
    Bad token for search_for_add_data_segment
    """
    response = await http_client_test.post(
        f"/data_segment/search_for_add_data_segment"
        f"?data_type=raw%20data&page_num=1&page_size=20"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_search_for_data_segment_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for search_for_add_data_segment
    """
    response = await http_client_test.post(
        f"/data_segment/search_for_add_data_segment"
        f"?data_type=raw%20data&page_num=1&page_size=20&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}


@pytest.mark.asyncio
async def test_search_for_data_segment_no_permission(
        http_client_test, test_college_validation, access_token,
        test_create_data_segment,
        setup_module):
    """
    No permission for search for_add_data_segment
    """
    response = await http_client_test.post(
        f"/data_segment/search_for_add_data_segment"
        f"?data_type=raw%20data&page_num=1&page_size=20"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_search_for_data_segment_success(
        http_client_test, test_college_validation,
        college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Get search_add_data_segment response
    """
    response = await http_client_test.post(
        f"/data_segment/search_for_add_data_segment"
        f"?data_type=raw%20data&page_num=1&page_size=20"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get raw data details."
