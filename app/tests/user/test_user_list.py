"""
This file contains test cases of get user list.
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_user_list(
        http_client_test, setup_module, test_college_validation, access_token,
        college_super_admin_access_token, college_counselor_access_token):
    """
    Different test cases of get lead profile header data.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        access_token: A fixture which create student if not exist and
            return access token of student.
        super_admin_access_token: A fixture which create super admin if not
            exist and return access token of super admin.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.

    Assertions:\n
        response status code and json message.
    """
    # Test case -> not authenticated if user not logged in
    response = await http_client_test.get(f"/user/list/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get("_id"))
    # Test case -> bad token for get user list
    response = await http_client_test.get(
        f"/user/list/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Test case -> field required for get user list
    response = await http_client_test.get(
        f"/user/list/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Type must be required "
                                         "and valid."}

    # Test case -> for get user list
    response = await http_client_test.get(
        f"/user/list/?user_type=college_counselor&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "List of users fetched successfully."

    # Test case -> for get user list
    response = await http_client_test.get(
        f"/user/list/?user_type=college_super_admin&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Test case -> Required college id for get user list.
    response = await http_client_test.get(
        f"/user/list/?user_type=super_admin&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == ("College Id must be required "
                                         "and valid.")

    # Test case -> Invalid college id for get user list.
    response = await http_client_test.get(
        f"/user/list/?user_type=super_admin&college_id=123&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Test case -> Invalid college id for get user list.
    response = await http_client_test.get(
        f"/user/list/?user_type=super_admin&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
