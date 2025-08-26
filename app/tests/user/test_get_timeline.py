"""
This file contains test cases of get users timeline
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_users_timeline_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/user/timeline/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_users_timeline_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get all college user details
    """
    response = await http_client_test.get(
        f"/user/timeline/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_users_timeline(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_add_timeline
):
    """
    Get users timeline
    """
    response = await http_client_test.get(
        f"/user/timeline/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == 'Get users timeline.'
    assert response.json()["data"] is not None


@pytest.mark.asyncio
async def test_get_users_timeline_by_pagination(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_add_timeline
):
    """
    Get users timeline by pagination
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_timeline_collection.delete_many({})
    response = await http_client_test.get(
        f"/user/timeline/?page_num=1&page_size=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == 'Get users timeline.'
    assert response.json()["data"] is not None
    assert response.json()["pagination"]['next'] is None


@pytest.mark.asyncio
async def test_get_users_timeline_by_pagination_no_found(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module
):
    """
    Users timeline not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_timeline_collection.delete_many({})
    response = await http_client_test.get(
        f"/user/timeline/?page_num=1&page_size=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == 'Get users timeline.'
    assert response.json()["data"] == []
    assert response.json()["pagination"]['next'] is None


@pytest.mark.asyncio
async def test_get_users_timeline_no_permission(
        http_client_test,
        test_college_validation,
        access_token,
        setup_module
):
    """
    No permission for get all college user details
    """
    response = await http_client_test.get(
        f"/user/timeline/?page_num=1&page_size=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
