"""
This file contains test cases of get the scholarship overview details API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_scholarship_overview_details(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation, application_details, test_course_validation):
    """
    Different test cases of get the scholarship overview details.

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
        test_scholarship_validation: A fixture which create scholarship if not exist and return scholarship data.
        application_details: A fixture which create application if not exist and return application data.
        test_course_validation: A fixture which create course if not exists and return course data.

    Assertions:\n
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))
    obj_application_id = application_details.get('_id')
    application_id = str(obj_application_id)
    default_scholarship_id = str(test_scholarship_validation.get('_id'))

    # Not authenticated for get the scholarship overview details.
    response = await http_client_test.post(f"/scholarship/overview_details/?college_id={college_id}"
                                           f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required application_id for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required and valid."}

    # No permission for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}"
        f"&application_id={application_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Default Scholarship Id must be required and valid."}

    # No permission for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}&"
        f"default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    def validate_successful_response(temp_response):
        assert response.status_code == 200
        assert temp_response.json()['message'] == "Get the scholarship overview details."
        temp_data = temp_response.json()["data"]
        for field_name in ["program_fee", "default_scholarship_name", "default_scholarship_amount",
                           "custom_scholarship_name", "custom_scholarship_amount", "fees_after_waiver"]:
            assert field_name in temp_data

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": obj_application_id}, {"$set": {"current_stage": 2}})

    # Get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    validate_successful_response(response)

    # Invalid application id for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id=123"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Application id `123` must be a 12-byte input or a 24-character hex string"

    # Invalid default scholarship id for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&default_scholarship_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == ("Default scholarship id `123` must be a 12-byte input or a 24-character "
                                         "hex string")

    # Invalid college id for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id=123&application_id={application_id}"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id=123456789012345678901234&application_id={application_id}"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get the scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?application_id={application_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    program_fee = test_course_validation.get("course_specialization")[1].get("spec_fee_info", {}).get(
        "registration_fee", 100000)

    # Invalid waiver type when get the scholarship overview details through custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}&waiver_type=test"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Waiver Type must be required and valid.'}

    # Invalid percentage when get the scholarship overview details through custom scholarship percentage.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Percentage&waiver_value=101&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Custom scholarship percentage should be less than or equal to 100.'}

    # Exceeding fee when get the scholarship overview details through custom scholarship percentage.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Percentage&waiver_value=100&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Default and custom scholarship amount exceeding program fee amount."}

    # Get the scholarship overview details through custom scholarship percentage.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Percentage&waiver_value=1&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    validate_successful_response(response)

    # Get the scholarship overview details through custom scholarship amount.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Percentage&waiver_value=1&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    validate_successful_response(response)

    # Invalid program fee when Get the scholarship overview details through custom scholarship amount.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Amount&waiver_value={program_fee + 1}&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': f'Custom Scholarship amount should be less than or equal to {program_fee}.'}

    # Scholarship information not found when get scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&default_scholarship_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'Default scholarship not found id: 123456789012345678901234'}

    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": obj_application_id}, {"$set": {"current_stage": 1.25, "offered_scholarship_info": {}}})

    # Get the scholarship overview details through custom scholarship amount.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id={application_id}"
        f"&waiver_type=Percentage&waiver_value=1&default_scholarship_id={default_scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': "Make sure default scholarship is associated with applicant."}

    await DatabaseConfiguration().studentApplicationForms.delete_many({})

    # Application information not found when get scholarship overview details.
    response = await http_client_test.post(
        f"/scholarship/overview_details/?college_id={college_id}&application_id=123456789012345678901234"
        f"&default_scholarship_id={default_scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'Application not found id: 123456789012345678901234'}
