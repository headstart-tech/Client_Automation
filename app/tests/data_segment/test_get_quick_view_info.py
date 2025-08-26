"""
This file contains test cases regarding for get quick view information of
data segments.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_quick_view_info(
        http_client_test, test_college_validation, access_token,
        college_super_admin_access_token, setup_module
):
    """
    Different test cases of get quick view information of data segments.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        access_token: A fixture which create student if not exist
            and return access token for student.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        test_create_data_segment: A fixture which return data segment details.

    Assertions:\n
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get quick view information of data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id when try to get quick view information of
    # data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}

    # No permission for get quick view information of data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Invalid college id for get quick view information of data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id=1234567890&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found when try to get quick view information of
    # data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    columns = ["total_data_segments", "active_data_segments",
                "closed_data_segments", "lead_data_segments",
                "application_data_segments", "raw_data_segments",
                "communication_info"]
    # Get quick view information of data segments.
    response = await http_client_test.get(
        f"/data_segments/quick_view_info/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the data segment quick " \
                                         "view data."
    for key in columns:
        assert key in response.json()["data"]

        # Get quick view information of data segments.
        response = await http_client_test.get(
            f"/data_segments/quick_view_info/?college_id={college_id}&"
            f"status=Active&feature_key={feature_key}",
            headers={
                "Authorization": f"Bearer {college_super_admin_access_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Get the data segment quick " \
                                             "view data."
        for name in columns:
            assert name in response.json()["data"]
