"""
This file contains test cases of update scholarship status API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_check_scholarship_exists_or_not(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation):
    """
    Different test cases of update scholarship status.

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
    # Not authenticated for update scholarship status.
    response = await http_client_test.put(f"/scholarship/update_status/?college_id={college_id}"
                                          f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required status for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status must be required and valid."}

    # Required scholarship_id for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Scholarship Id must be required and valid."}

    scholarship_id = str(test_scholarship_validation.get('_id'))
    # No permission for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Update scholarship status to Active.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Scholarship status updated successfully to Active."

    # Update scholarship status to Closed.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Closed"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Scholarship status updated successfully to Closed."

    # Update scholarship status to Closed.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=xyz&scholarship_id={scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Status must be required and valid."

    # Invalid college id for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id=123&status=Active&scholarship_id={scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id=123456789012345678901234&status=Active&scholarship_id="
        f"{scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?status=Active&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scholarship_collection.delete_many({})
    # Scholarship not found when update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == f"Scholarship not found id: {scholarship_id}"

    # Invalid scholarship id for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active&scholarship_id=123"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Scholarship id `123` must be a 12-byte input or a 24-character hex string"

    # Wrong scholarship id for update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?college_id={college_id}&status=Active&"
        f"scholarship_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Scholarship not found id: 123456789012345678901234"

    # Required scholarship id when update scholarship status.
    response = await http_client_test.put(
        f"/scholarship/update_status/?status=Active&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Scholarship Id must be required and valid.'}
