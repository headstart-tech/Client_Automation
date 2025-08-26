"""
This file contains test cases regarding for get count of data segment entities.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_entities_count(
        http_client_test, test_college_validation, access_token,
        college_super_admin_access_token, setup_module,
        test_create_data_segment):
    """
    Different test cases of get count of data segment entities.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - access_token: A fixture which create student if not exist
            and return access token for student.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - test_automation_rule_details_validation: A fixture which create data
            segment, create automation rule and return automation rule details.

    Assertions:
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))
    # Bot authenticated user tried to get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Required body for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required "
                                         "and valid."}

    # No permission for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_create_data_segment
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Invalid college id for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id=1234567890&feature_key={feature_key}",
        json=test_create_data_segment,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte "
                                         "input or a 24-character hex string"}

    # College not found for get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id="
        f"123456789012345678901234&feature_key={feature_key}", json=test_create_data_segment,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Get count of data segment entities.
    response = await http_client_test.post(
        f"/data_segment/count_of_entities/?college_id={college_id}&feature_key={feature_key}",
        json=test_create_data_segment,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "entities_count" in response.json()
