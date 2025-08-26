"""
This file contains test cases regarding for update data segments by ids.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_data_segments_by_ids(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_create_data_segment
):
    """
    Different test cases of download data segments by ids.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
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
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id when try to update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}

    # Required data segments ids for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Data Segments Ids must be required "
                                         "and valid."}

    # Required status for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"data_segments_ids": ["123"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status must be required and valid."}

    # No permission for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"data_segments_ids": ["123"], "status": "string"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Invalid college id for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": ["123"], "status": "string"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found when try to update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": ["123"], "status": "string"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().data_segment_collection.delete_many({})

    # Invalid data segment id update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": ["123"], "status": "string"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Data segment id `123` must be a "
                                         "12-byte input or a 24-character "
                                         "hex string"}

    # Wrong data segment id update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": ["123456789012345678901234"],
              "status": "active"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Data segments not found by "
                                         "provided ids."}

    await http_client_test.post(
        f"/data_segment/create/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment
    )

    data_segment = await DatabaseConfiguration().data_segment_collection.\
        find_one({})

    # Update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": [str(data_segment.get("_id"))],
              "status": "active"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Data segments status updated "
                                          "successfully."}

    # Wrong status for update data segments by ids.
    response = await http_client_test.put(
        f"/data_segments/change_status/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"data_segments_ids": [str(data_segment.get("_id"))],
              "status": "test"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Make sure provided status is "
                                         "correct."}
