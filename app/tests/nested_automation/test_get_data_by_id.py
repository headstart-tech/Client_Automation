"""
This file contains test cases related to get automation data by id.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_automation_top_bar_details(
        http_client_test, setup_module, test_college_validation, access_token,
        college_super_admin_access_token, test_automation_validation,
        start_end_date):
    """
    Different test cases of get automation data by id.

    Params:\n
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - access_token: A fixture which create student if not exist
            and return access token of student.
        - college_super_admin_access_token: A fixture which create college
            super admin if not exist and return access token of college
            super admin.
        - test_automation_validation: A fixture which create automation
            if not exist and return automation rule data.
        - start_end_date: A fixture which return last 3 month date_range.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated test case
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get('_id'))
    automation_id = str(test_automation_validation.get('_id'))
    # Bad credentials to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # College id required to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/?"
        f"automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # College not found to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id=123456789012345678901234&"
        f"automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Invalid college id to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id=1234&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # No permission to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

    # Get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get the automation data by id."
    for item in ["automation_details", "automation_node_edge_details",
                 "automation_status", "template"]:
        assert item in response.json()["data"]
    for item in ["automation_name", "data_type", "releaseWindow", "date",
                 "days", "data_segment", "data_count", "filters"]:
        assert item in response.json()["data"]["automation_details"]

    # Automation id required to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Automation Id must be required and "
                                         "valid."}

    # Automation not found to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id={college_id}&automation_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Automation not found id: "
                                         "123456789012345678901234"}

    # Automation id invalid to get automation data by id
    response = await http_client_test.get(
        f"/nested_automation/get_data_by_id/"
        f"?college_id={college_id}&automation_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "Automation id `1234` must be a 12-byte input or a "
                      "24-character hex string"}
