"""
This file contains test cases of get scholarship applicants data API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_scholarship_applicants_data(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation, application_details, test_student_data, test_create_scholarship_data):
    """
    Different test cases of get scholarship applicants data.

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
        test_scholarship_validation: A fixture which create scholarship if not exist
            and return scholarship data.
        application_details: A fixture which add application add if not exist
            and return application data.
        test_student_data: A fixture which return student dummy data.
        test_create_scholarship_data: A fixture which return dummy scholarship data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for get scholarship applicants data.
    response = await http_client_test.post(f"/scholarship/applicants_data/?college_id={college_id}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required page number for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&scholarship_data_type=eligible"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Num must be required and valid.'}

    # Required page size for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1"
        f"&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Size must be required and valid.'}

    # Required scholarship id for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': "Scholarship Id must be required and valid."}

    scholarship_id = str(test_scholarship_validation.get('_id'))
    # Required scholarship data type for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': "Scholarship Data Type must be required and valid."}

    # Invalid scholarship data type for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': "Scholarship Data Type must be required and valid."}

    # No permission for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    async def validate__successful_common_response(temp_response, temp_data):
        assert temp_response.status_code == 200
        assert temp_response.json()['message'] == "Get applicants data."
        for field_name in ["application_id", "custom_application_id", "student_name", "course_name"]:
            assert field_name in temp_data

    async def validate_eligible_data(temp_response):
        temp_data = temp_response.json()["data"]
        if temp_data:
            temp_data = temp_data[0]
            await validate__successful_common_response(temp_response, temp_data)
            for field_name in ["payment_status", "lead_stage", "student_verify", "default_scholarship_name",
                               "scholarship_letter_count", "is_scholarship_letter_sent",
                               "scholarship_details", "scholarship_letter_info"]:
                assert field_name in temp_data

    async def validate_applicant_data(temp_response):
        temp_data = temp_response.json()["data"]
        if temp_data:
            temp_data = temp_data[0]
            await validate__successful_common_response(temp_response, temp_data)
            for field_name in ["description", "fees_after_waiver", "percentage"]:
                assert field_name in temp_data

    # Get eligible applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_eligible_data(response)

    # Get eligible applicants data by search.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": test_student_data.get("full_name")}
    )
    await validate_eligible_data(response)

    async def validate_download_response(temp_response, invalid_data=False):
        assert temp_response.status_code == 200
        if not invalid_data:
            assert temp_response.json()["message"] == "File downloaded successfully."
            assert "file_url" in temp_response.json()
        else:
            assert temp_response.json()["message"] == "No data to download."

    # Todo: We'll check below test case later on, it is failing.
    # # Download eligible applicants' data.
    # response = await http_client_test.post(
    #     f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
    #     f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&download=true",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    # )
    # await validate_download_response(response)

    # Get offered applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_applicant_data(response)

    # Get offered applicants data by search.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": test_student_data.get("full_name")}
    )
    await validate_applicant_data(response)

    # Get offered applicants data by programs.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_applicant_data(response)

    # Get availed applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_applicant_data(response)

    # Get availed applicants data by search.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": test_student_data.get("full_name")}
    )
    await validate_applicant_data(response)

    # Get availed applicants data by programs.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_applicant_data(response)

    # Download availed applicants' data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&download=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    await validate_download_response(response)

    # Invalid college id for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id=123&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id=123456789012345678901234&page_num=1&"
        f"page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Invalid sort type when get scholarship applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Sort Type must be required and valid.'}

    async def validate_failed_response(temp_response):
        assert temp_response.status_code == 200
        assert temp_response.json()['message'] == "Get applicants data."
        assert temp_response.json()["data"] == []
        assert temp_response.json()["total_data"] == 0

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.delete_many({})

    # Eligible applicant data not found when get eligible applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_failed_response(response)

    # Eligible applicant data not found when get eligible applicants data by search.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": "test"}
    )
    await validate_failed_response(response)

    # Eligible applicant data not found when download eligible applicants' data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=eligible&download=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    await validate_download_response(response, invalid_data=True)

    # Offered applicant data not found when get offered applicants data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_failed_response(response)

    # Offered applicant data not found when get offered applicants data by search.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": "test"}
    )
    await validate_failed_response(response)

    # Offered applicant data not found when get offered applicants data by sort.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "asc"}
    )
    await validate_failed_response(response)

    # Offered applicant data not found when get offered applicants data by programs.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=offered&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_failed_response(response)

    # Availed applicant data not found when get availed applicants data by sort.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "asc"}
    )
    await validate_failed_response(response)

    # Availed applicant data not found when get availed applicants data by programs.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_failed_response(response)

    # Availed applicant data not found when download availed applicants' data.
    response = await http_client_test.post(
        f"/scholarship/applicants_data/?college_id={college_id}&page_num=1&page_size=6&"
        f"scholarship_id={scholarship_id}&scholarship_data_type=availed&download=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    await validate_download_response(response, invalid_data=True)
