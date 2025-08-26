"""
This file contains test cases regarding with get all reports
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_reports(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, test_report_validation,
        test_schedule_report_validation, test_auto_schedule_report_validation):
    """
    Different test cases of get all reports.

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
        - test_report_validation: A fixture which delete all existing reports
            and create a new report.
        - test_schedule_report_validation: A fixture which delete all existing
            reschedule reports and create a new reschedule report.
        - test_auto_schedule_report_validation: A fixture which auto schedule
            reports and create a new auto schedule report.

    Assertions:\n
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/reports/?"
                                           f"college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get all reports
    response = await http_client_test.post(
        f"/reports/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required page number for get all reports
    response = await http_client_test.post(
        f"/reports/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Num must be required and valid."

    # Required page size for get all reports
    response = await http_client_test.post(
        f"/reports/?page_num=1&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Size must be required and valid."

    response_keys = ["statement", "report_id", "request_id", "report_type",
                     "format", "requested_on", "user_type", "requested_by",
                     "requested_by_name", "record_count", "advance_filter"]

    async def check_common_assertions(test_response):
        assert test_response.status_code == 200
        assert test_response.json()["count"] == 100
        assert test_response.json()["pagination"]['next'] is None
        assert test_response.json()["pagination"]['previous'] is None
        assert test_response.json()["message"] == "Get reports."

    async def validate_successful_result(test_response):
        await check_common_assertions(test_response)
        data = test_response.json()['data']
        if data and len(data) >= 1:
            for key in response_keys:
                assert key in data[0]

    async def validate_invalid_data(test_response):
        await check_common_assertions(test_response)
        assert test_response.json()["total"] == 0
        assert test_response.json()["data"] == []

    # Get all reports
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # Get all reschedule reports
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id={college_id}&"
        f"reschedule_report=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # Get reschedule reports by search pattern
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&reschedule_report=true&search_pattern=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # Get reschedule reports not found by search pattern
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&reschedule_report=true&search_pattern=schedule&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_invalid_data(response)

    # Get reports by search pattern
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&search_pattern=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # Reports not found by search pattern
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&search_pattern=xyz&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # All reports not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().report_collection.delete_many(
        {'reschedule_report': {"$in": [False, None]},
         "is_auto_schedule": {"$in": [False, None]}})
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_invalid_data(response)

    # All reschedule reports not found
    await DatabaseConfiguration().report_collection.delete_many(
        {'reschedule_report': True})
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id={college_id}&"
        f"reschedule_report=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_invalid_data(response)

    # Get all auto schedule reports
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&auto_schedule_reports=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    response_keys.extend(["trigger_by", "interval", "next_trigger_time",
                          "last_trigger_time"])
    await validate_successful_result(response)

    # Get auto schedule reports by search pattern
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&auto_schedule_reports=true&search_pattern=auto&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_successful_result(response)

    # Auto schedule reports not found by search_pattern
    await DatabaseConfiguration().report_collection.delete_many(
        {'is_auto_schedule': True})
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&auto_schedule_reports=true&search_pattern=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_invalid_data(response)

    # Auto schedule reports not found for current user
    response = await http_client_test.post(
        f"/reports/?page_num=1&page_size=100&college_id="
        f"{college_id}&auto_schedule_reports=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    await validate_invalid_data(response)
