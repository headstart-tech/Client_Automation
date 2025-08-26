"""
This file contains test cases related to get season list
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_season_list_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/college/season_list/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_season_list_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for get season list
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/season_list/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_season_list_no_permission(
        http_client_test, access_token, test_college_data, setup_module
):
    """
    Test case -> no permission for get season list
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/college/season_list/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_season_list(http_client_test, college_super_admin_access_token,
                           test_college_data, setup_module,
                           test_college_validation):
    """
    Test case -> for get season list
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/college/season_list/?name={test_college_validation.get('name')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get list of season."


@pytest.mark.asyncio
async def test_season_list_wrong_college_id(http_client_test,
                                            college_super_admin_access_token,
                                            setup_module):
    """
    Test case -> wrong college id for get season list
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/college/season_list/?id=12345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"


@pytest.mark.asyncio
async def test_season_list_no_found(http_client_test,
                                    college_super_admin_access_token,
                                    setup_module):
    """
    Test case -> college not found for get season list
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.get(f"/college/season_list/?feature_key={feature_key}",
                                          headers={
                                              "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "College not found."
