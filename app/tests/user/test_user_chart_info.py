"""
This file contains test cases for get/download user chart information.
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_or_download_user_chart_info(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, access_token
):
    """
    Different test cases for get/download user chart information.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        access_token: A fixture which create student if not exist
            and return access token for student.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/user/chart_info/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "College Id must be required and " \
                                        "valid."

    college_id = str(test_college_validation.get('_id'))
    # No permission for get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the user chart information."
    for name in ["userChart", "dataChart"]:
        assert name in response.json()["data"]
        assert "labels" in response.json()["data"][name]
        assert "data" in response.json()["data"][name]

    # Invalid college id for get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input" \
                                        " or a 24-character hex string"

    # Wrong college id for get user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Download user chart information
    response = await http_client_test.post(
        f"/user/chart_info/?college_id={college_id}&download_data=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File downloaded successfully."
    assert "file_url" in response.json()
