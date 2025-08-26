"""
This file contains test cases related to get automation communication data.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_automation_communication_Data(
        http_client_test, setup_module, test_college_validation, access_token,
        college_super_admin_access_token, test_automation_validation,
        start_end_date):
    """
    Different test cases of get automation communication data.

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
    response = await http_client_test.post(
        f"/nested_automation/communication_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get('_id'))
    automation_id = str(test_automation_validation.get('_id'))

    # Bad credentials to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # College id required to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/?"
        f"automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # College id not found to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id=123456789012345678901234&"
        f"automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # College id invalid to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id=1234&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # No permission to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

    # Automation not found to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'Automation not found id: '
                                         '123456789012345678901234'}

    # Automation id invalid to get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail":
                                   "Automation id `1234` must be a 12-byte "
                                   "input or a 24-character hex string"}

    # Get automation communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get the automation communication " \
                                         "data."

    # Get automation email communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&email=true&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get the automation communication " \
                                         "data."
    common_temp = ["id", "template_name", "sent", "delivered"]
    email_temp = common_temp + ["opened", "clicked", "complaint_rate",
                                "unsubscribe_rate"]
    if response.json()["data"]:
        for item in email_temp:
            assert item in response.json()["data"][0]

    # Get automation s,s communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&sms=true&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get the automation communication " \
                                         "data."
    sms_temp = common_temp + ["sender_id", "sms_type", "dlt_id", "content"]
    if response.json()["data"]:
        for item in sms_temp:
            assert item in response.json()["data"][0]

    # Get automation whatsapp communication data
    response = await http_client_test.post(
        f"/nested_automation/communication_data/"
        f"?college_id={college_id}&automation_id={automation_id}&whatsapp=true&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()[
               'message'] == "Get the automation communication " \
                             "data."
    whatsapp_temp = common_temp + ["tag", "content", "click_rate", "content"]
    if response.json()["data"]:
        for item in whatsapp_temp:
            assert item in response.json()["data"][0]
