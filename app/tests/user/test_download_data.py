"""
This file contains test cases for download users data by IDs
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_download_users_data_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(f"/user/download_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_download_users_data_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for download users data by IDs
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/user/download_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# @pytest.mark.asyncio
# async def test_download_users_data(
#     http_client_test,
#     college_super_admin_access_token,
#     setup_module,
# ):
#     """
#     Test case -> for download users data without passing ids
#     :param http_client_test:
#     :param college_super_admin_access_token:
#     :return:
#     """
#     response = await http_client_test.post(
#         f"/user/download_data/?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Data downloaded"}


@pytest.mark.asyncio
async def test_download_users_data_by_ids(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_user_validation,
):
    """
    Test case -> for download users data by IDs
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/user/download_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[f"{str(test_user_validation['_id'])}"],
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Data downloaded"}


@pytest.mark.asyncio
async def test_download_users_data_wrong_ids(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_user_validation,
):
    """
    Test case -> wrong user id for download users data by IDs
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/user/download_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["string"],
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "User id must be a 12-byte input or a 24-character hex string"
    }


@pytest.mark.asyncio
async def test_download_users_data_no_permission(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> no permission for download users data by IDs
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/user/download_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
