"""
This file contains test cases for get raw data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_raw_data_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/manage/get_all_raw_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_raw_data_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get raw data
    """
    response = await http_client_test.post(
        f"/manage/get_all_raw_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_raw_data_required_page_number(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for get raw data
    """
    response = await http_client_test.post(
        f"/manage/get_all_raw_data/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_raw_data_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page size for get raw data
    """
    response = await http_client_test.post(
        f"/manage/get_all_raw_data/?page_num=1&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_get_raw_data(
        http_client_test,
        test_college_validation,
        super_admin_access_token,
        setup_module,
):
    """
    Get raw data
    """
    response = await http_client_test.post(
        f"/manage/get_all_raw_data/?page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
