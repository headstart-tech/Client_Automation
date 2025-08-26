"""
This file contains test cases of get preference data.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_preference_data(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, application_details, start_end_date):
    """
    Different test cases of get preference data.

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
        application_details: A fixture which create application if not exist
            and return application details.
        start_end_date: A fixture which useful for get date range.

    Assertions:\n
        response status code and json message.
    """
    # Test case -> not authenticated if user not logged in
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get("_id"))
    # Test case -> bad token for change preference order
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    def validate_successful_response(valid_response, download_data=False):
        """
        Validate successful response of test case.
        """
        assert valid_response.status_code == 200
        data = valid_response.json()
        if download_data:
            assert data["message"] == "File downloaded successfully."
            assert "file_url" in data
        else:
            assert data["message"] == "Get the preference wise information."
            for item in ["header", "data", "total"]:
                assert item in data

    # Test case -> get preference wise data based on leads
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response)

    # Test case -> get preference wise data based on applications
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&"
        f"data_for=Applications&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response)

    # Test case -> get preference wise data by filter program_name
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"program_name": [{"course_id": str(application_details.get("course_id")),
                               "spec_name1": application_details.get("spec_name")}]}
    )
    validate_successful_response(response)

    # Test case -> get preference wise data by filter date range
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"date_range": start_end_date}
    )
    validate_successful_response(response)

    # Test case -> get preference wise data by sorting course_name
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": True, "sort_name": "course_name", "sort_type": "dsc"}
    )
    validate_successful_response(response)

    # Test case -> Required college id for get preference wise data based on leads
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == ("College Id must be required "
                                         "and valid.")

    # Test case -> Invalid college id get preference wise data based on leads
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?&college_id=123&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Test case -> Wrong college id for get preference wise data based on leads
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Test case -> download preference wise data based on leads
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&"
        f"download_data=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response, download_data=True)

    # Test case -> download preference wise data based on applications
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&"
        f"download_data=true&data_for=Applications&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response, download_data=True)

    # Test case -> download preference wise data based on applications
    response = await http_client_test.post(
        f"/admin/preference_wise_data/?college_id={college_id}&"
        f"download_data=true&data_for=Applications&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response, download_data=True)
