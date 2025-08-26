"""
This file contains test cases of generate/save report.
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_generate_request_data(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, test_generate_report_data):
    """
    Different test cases of generate/save report.

    Params:\n
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - college_super_admin_access_token: A fixture which create college
            super admin if not exist and return access token of college super
            admin.
        - test_generate_report_data: A fixture which return generate report
            data.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/reports/generate_request_data/?feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == \
           {"detail": "College Id must be required and valid."}

    college_id = str(test_college_validation.get('_id'))
    # No permission for generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == \
           {"detail": "Request Data must be required and valid."}

    response_keys = ["report_id", "request_id", "report_type",
                     "format", "requested_on", "user_type", "requested_by",
                     "requested_by_name"]
    # Generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 200
    assert response.json()["request_data"]["status"] == "In progress"
    for key in response_keys:
        assert key in response.json()["request_data"]

    # Generate request data with payload
    test_generate_report_data['report_name'] = "test2"
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"state_code": ["MH"]}
        },
    )
    assert response.status_code == 200
    assert response.json()["request_data"]["status"] == "In progress"

    # Save report
    test_generate_report_data.update(
        {'save_template': True})
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data }
    )
    assert response.status_code == 200
    assert response.json()["request_data"]["status"] is None

    # Generate request data with wrong state format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"state_code": "MH"}
        }
    )
    assert response.status_code == 400
    assert response.json()[
               "detail"] == "State Code must be required and valid."

    # Generate request data with wrong city format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"city_name": "Pune"}
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "City Name must be required and valid."

    # Generate request data with wrong source format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"source_name": "google"}
        },
    )
    assert response.status_code == 400
    assert response.json()[
               "detail"] == "Source Name must be required and valid."

    # Generate request data with wrong lead format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"lead_name": "Fresh Lead"}
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Lead Name must be required and valid."

    # Generate request data with wrong counselor id format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"counselor_id": 123}
        },
    )
    assert response.status_code == 400
    assert response.json()[
               "detail"] == "Counselor Id must be required and valid."

    # Generate request data with wrong payment status format in payload
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "request_data": test_generate_report_data,
            "payload": {"payment_status": 123}
        },
    )
    assert response.status_code == 400
    assert response.json()[
               "detail"] == "Payment Status must be required and valid."

    # Reschedule report
    test_generate_report_data.update(
        {'reschedule_report': True, 'schedule_value': 1,
         'schedule_type': 'Day'})
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 200
    assert response.json()["request_data"]["status"] is None

    # Invalid college id for generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"

    # Wrong college id for generate request data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    from app.database.configuration import DatabaseConfiguration
    report_data = await DatabaseConfiguration().report_collection.find_one({})
    # Update the report data by report id
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&"
        f"report_id={str(report_data.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Report data updated successfully."}

    # Invalid report id for update the report data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&"
        f"report_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Report id `123` must be a 12-byte " \
                                        "input or a 24-character hex string"

    # Wrong report id for update the report data
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&"
        f"report_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Report data not found id: " \
                                        "123456789012345678901234"

    # Generate request data
    today_date = datetime.datetime.utcnow()
    format_date = today_date.strftime("%Y-%m-%d")
    test_generate_report_data.update(
        {"report_name": "auto_reschedule", 'reschedule_report': False,
         'save_template': False, "is_auto_schedule": True,
         "generate_and_reschedule": {"trigger_by": "Weekly", "interval": 2,
                                     "date_range": {"start_date": format_date,
                                                    "end_date": format_date
                                                    }}})
    response = await http_client_test.post(
        f"/reports/generate_request_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data}
    )
    assert response.status_code == 200
    assert response.json()["request_data"]["status"] == "In progress"
    for key in response_keys:
        assert key in response.json()["request_data"]
