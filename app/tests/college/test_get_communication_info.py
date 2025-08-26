"""
This file contains test cases related to get communication info of college
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_communication_info_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/college/communication_info/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_communication_info_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for get communication info of college
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_communication_info_no_permission(
        http_client_test, access_token, test_college_data, setup_module
):
    """
    Test case -> no permission for get communication info of college
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_communication_info_by_id(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> for get college_details by college_id
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get communication info of college."


@pytest.mark.asyncio
async def test_get_communication_info_by_name(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> for get college_details by college_name
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?college_name={test_college_validation.get('name')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get communication info of college."


@pytest.mark.asyncio
async def test_get_communication_info_by_id_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> for get college_details by college_id not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "College not found. Make sure college_id or college_name is correct."


@pytest.mark.asyncio
async def test_get_communication_info_by_name_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> for get college_details by college_name not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/communication_info/?college_name=wrong_name&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "College not found. Make sure college_id or college_name is correct."
