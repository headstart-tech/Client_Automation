"""
This file contains test cases related to lead profile header.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_lead_profile_header(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, application_details):
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
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        application_details: A fixture which add application add if not exist
            and return application data.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated for get lead profile header
    college_id = str(test_college_validation.get('_id'))
    response = await http_client_test.get(
        f"/lead/lead_profile_header/62a057ef1ec1188907d262a3?"
        f"college_id={college_id}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Invalid credentials for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/62a057ef1ec1188907d262a3?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/{str(application_details.get('_id'))}?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    data = response.json()["data"][0]
    for item in ["basic_info", "communication_status", "telephony_status",
                 "assigned_counselor", "upcoming_followup", "lead_source",
                 "sec_ter_source", "utm_campaign_name",
                 "utm_campaign_name_extra", "utm_medium", "utm_medium_extra",
                 "lead_age", "lead_age_date", "tags"]:
        assert item in data

    # Application not found for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/62a057ef1ec1188907d262a2?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    # Invalid application id for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/12345678901234567890?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json()["detail"] == "Application id must be a 12-byte "
                                         "input or a 24-character hex string")

    # College not found for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/62a057ef1ec1188907d262a2?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Invalid college id for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/12345678901234567890?"
        f"college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json()["detail"] == "College id must be a 12-byte "
                                         "input or a 24-character hex string")

    # Required college id for get lead profile header
    response = await http_client_test.get(
        f"/lead/lead_profile_header/12345678901234567890?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert (response.json()["detail"] == "College Id must be required and "
                                         "valid.")
