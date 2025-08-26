"""
This file contains test cases related to general additional details route.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_general_additional_details(http_client_test, setup_module, test_college_validation,
                                          college_super_admin_access_token, access_token,
                                          test_student_data,
                                          test_student_validation,
                                          test_college_configuration_data,
                                          test_client_automation_college_id):
    """
    Different test cases of get utm campaign list.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
            after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - access_token: A fixture which create student if not exist and return access token of student.
        - test_student_data: A fixture which return student dummy data.
        - test_student_validation: A fixture which create student if not exist
            and return student data.

    Assertions:\n
        response status code and json message.
    """

    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/college/additional_details?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token.
    response = await http_client_test.post(
        f"/college/additional_details?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json={})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Add general additional data
    response = await http_client_test.post(
        f"/college/additional_details?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "logo_transparent": "https://example.com/",
            "fab_icon": "https://example.com/",
            "student_dashboard_landing_page_link": "https://example.com/",
            "google_tag_manager_id": "string",
            "lead_stages": [
                {
                    "stage_name": "string",
                    "sub_lead_stage": [
                        "string"
                    ]
                }
            ],
            "lead_tags": [
                "string"
            ],
            "student_dashboard_domain": "https://example.com/",
            "campus_tour_video_url": "https://example.com/",
            "brochure_url": "https://example.com/",
            "payment_method": "icici_bank"
        })
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")

    response = await http_client_test.post(
        "/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_college_configuration_data,
        params={"college_id": test_client_automation_college_id},
    )
    assert response.status_code == 200

    # Approving the request
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 200
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"}
    # )
    # assert response.status_code == 200


    # Wrong college id.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id=12345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={})
    assert response.status_code == 422
    assert response.json()[
               'detail'] == ("College id must be a 12-byte input "
                             "or a 24-character hex string")

    # College not found.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={})
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college id for get utm medium data by source names
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}, json={})
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and valid."
