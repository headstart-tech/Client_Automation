"""
Test case for all the save report templates data set.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_unauthenticated_get_data(
    http_client_test,
    setup_module
):
    # Un-authorized user tried to use API.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_invalid_access_token(http_client_test, setup_module):

    # Pass invalid access token for get the data from API.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_without_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Required college id.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}


@pytest.mark.asyncio
async def test_invalid_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Invalid college id.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_wrong_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Wrong college id.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_get_valid_data_set(http_client_test, setup_module, college_super_admin_access_token, test_college_validation):

    response_key = [
        "report_type", "report_name", "format", "report_details", "payload",
        "advance_filter", "send_mail_recipients_info", "add_column",
        "generate_and_reschedule", "period", "requested_by",
        "requested_by_name", "report_send_to", "status", "requested_on",
        "request_finished_on", "schedule_created_on", "sent_mail",
        "is_auto_schedule", "interval", "trigger_by", "date_range"
    ]
    # Get the proper data set.
    response = await http_client_test.get(
        f"/reports/get_saved_report_templates/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the saved report template."
    
    if response.json()['total'] > 0:
        for key in response_key:
            assert key in response.json()['data'][0]
