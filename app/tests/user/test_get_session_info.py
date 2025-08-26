"""
This file contains test cases regarding get session info of users
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_session_info_not_authenticated(http_client_test, test_college_validation, setup_module,
                                                  test_student_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_session_info_bad_credentials(http_client_test, test_college_validation, setup_module,
                                                test_student_validation):
    """
    Bad token for get session info of users
    """
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_session_info_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_student_validation
):
    """
    No permission for get session info of users
    """
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_session_info_of_users_required_college_id(http_client_test, test_college_validation,
                                                             college_super_admin_access_token):
    """
    Required college id for get session info of users
    """
    response = await http_client_test.get(f"/user/session_info/?page_num=1&page_size=1&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_get_session_info_of_users_invalid_college_id(http_client_test, test_college_validation,
                                                            college_super_admin_access_token):
    """
    Invalid college id for get session info of users
    """
    response = await http_client_test.get(
        f"/user/session_info/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_session_info_of_users_college_not_found(http_client_test, test_college_validation,
                                                           college_super_admin_access_token):
    """
    College not found for get session info of users
    """
    response = await http_client_test.get(
        f"/user/session_info/?college_id=123456789012345678901234&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_session_info_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_student_validation
):
    """
    Session info of users not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().refresh_token_collection.delete_many({})
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Session info data not found."}


@pytest.mark.asyncio
async def test_get_session_info(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation, student_refresh_token
):
    """
    Session info of users not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().refresh_token_collection.delete_many({})
    await DatabaseConfiguration().refresh_token_collection.insert_one(
        {'user_id': test_counselor_validation.get("_id"),
         "user_type": test_counselor_validation.get("role", {}).get("role_name"),
         "user_email": test_counselor_validation.get("user_name"),
         'refresh_token': student_refresh_token.get("refresh_token"),
         "expiry_time": student_refresh_token.pop("expiry_time"), "issued_at": student_refresh_token.pop("issued_at"),
         "revoked": False,
         "college_info": [{"name": "test", "_id": test_counselor_validation.get("associated_colleges")[0]}]})

    # Without pagination
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get session info of users."
    assert response.json()["data"] != []
    assert response.json()["total"] == 1
    assert response.json()["count"] is None
    assert response.json()["pagination"] is None

    # With pagination
    response = await http_client_test.get(
        f"/user/session_info/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get session info of users."
    assert response.json()["data"] != []
    assert response.json()["total"] == 1
    assert response.json()["count"] == 25
    assert response.json()["pagination"] == {"next": None, "previous": None}
