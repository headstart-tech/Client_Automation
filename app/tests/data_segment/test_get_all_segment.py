"""
This file contains test cases regarding for get data segments.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_data_segments(
        http_client_test, setup_module, test_college_validation, access_token,
        college_super_admin_access_token, test_create_data_segment_helper
):
    """
    Different test cases of get data segments.

    Params:\n
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - access_token: A fixture which create student if not exist and
            return access token of student.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - test_create_data_segment_helper: A fixture which add data
            segment details if not exist and return data segment data.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/data_segments/?college_id={test_college_validation.get('_id')}&"
        f"page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id={test_college_validation.get('_id')}&"
        f"page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Field college id when try to get data segments
    response = await http_client_test.post(
        f"/data_segments/?page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # No permission for get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id={test_college_validation.get('_id')}&"
        f"page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Invalid college id for get data segment details
    response = await http_client_test.post(
        f"/data_segments/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found when try to get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id=123456789012345678901234&"
        f"page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    college_id = str(test_college_validation.get('_id'))
    columns = ['data_segment_id', 'data_segment_name',
               'data_segment_description', 'module_name',
               "raw_data_name", 'period', 'enabled', 'is_published',
               'created_by_id', "created_by_name", "created_on",
               "updated_by", "updated_by_name", "updated_on",
               "count_of_entities", "entities_data"]
    # Get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id={college_id}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get data segments."
    assert response.json()["data"] is not None
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    assert response.json()["pagination"] == {"next": None, "previous": None}

    # Required page number for get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id={college_id}&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Page Num must be required and valid."

    # Required page size for get data segments
    response = await http_client_test.post(
        f"/data_segments/?college_id={college_id}&"
        f"page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Page Size must be required and valid."

    # Get data segments by filter data_types
    response = await http_client_test.post(
        f"/data_segments/?college_id={college_id}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_types": ["Lead"]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get data segments."
    assert response.json()["data"] is not None
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    assert response.json()["pagination"] == {"next": None, "previous": None}

    # Get data segments by filter segment_type
    response = await http_client_test.post(
        f"/data_segments/?college_id={college_id}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"segment_type": "Dynamic"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get data segments."
    assert response.json()["data"] is not None
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    assert response.json()["pagination"] == {"next": None,
                                             "previous": None}
