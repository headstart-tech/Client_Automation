"""
This file contains test cases of get top bar summary data API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_scholarship_summary_data(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation):
    """
    Different test cases of get top bar summary data.

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
        access_token: A fixture which create student if not exist and return access token of student.
        test_scholarship_validation: A fixture which create scholarship if not exist
            and return scholarship data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for get top bar summary data.
    response = await http_client_test.post(f"/scholarship/get_summary_data/?college_id={college_id}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get scholarship summary data."
    for field_name in ["total_scholarships", "active_scholarships", "closed_scholarships",
                       "total_availed_amount"]:
        temp_data = response.json()["data"]
        assert field_name in temp_data
        assert temp_data[field_name] == (1 if field_name in ["total_scholarships", "closed_scholarships"] else 0)

    # Invalid college id for get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scholarship_collection.delete_many({})
    # Scholarship not found when get top bar summary data.
    response = await http_client_test.post(
        f"/scholarship/get_summary_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get scholarship summary data."
    assert response.json()['data'] == {}
