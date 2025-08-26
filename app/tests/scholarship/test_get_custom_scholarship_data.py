"""
This file contains test cases of get custom scholarship table information API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_custom_scholarship_table_information(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation, application_details, test_student_data):
    """
    Different test cases of get custom scholarship table information.

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

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for get custom scholarship table information.
    response = await http_client_test.post(f"/scholarship/get_give_custom_scholarship_table_data/"
                                           f"?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required page number for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Num must be required and valid.'}

    # Required page size for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}"
        f"&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Size must be required and valid.'}

    # No permission for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&page_num=1&"
        f"page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    async def validate_common_response(temp_response):
        assert temp_response.status_code == 200
        assert temp_response.json()['message'] == "Get give custom scholarship table data."

    async def validate_successful_response(temp_response):
        await validate_common_response(temp_response)
        temp_data = temp_response.json()["data"][0]
        for field_name in ["application_id", "custom_application_id", "student_name", "payment_status",
                           "offer_letter_sent", "lead_stage", "student_verify", "course_name"]:
            assert field_name in temp_data

    # Get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&page_num=1"
        f"&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_successful_response(response)

    # Get scholarship table information by search.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&page_num=1"
        f"&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": test_student_data.get("full_name")}
    )
    await validate_successful_response(response)

    # Invalid college id for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id=123&page_num=1"
        f"&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id=123456789012345678901234&"
        f"page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    async def validate_failed_response(temp_response):
        await validate_common_response(temp_response)
        assert response.json()['data'] == []
        assert response.json()['total_data'] == 0

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.delete_many({})
    # Scholarship data not found when get custom scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&page_num=1"
        f"&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_failed_response(response)

    # Scholarship data not found when get custom scholarship table information by search.
    response = await http_client_test.post(
        f"/scholarship/get_give_custom_scholarship_table_data/?college_id={college_id}&page_num=1"
        f"&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": "test"}
    )
    await validate_failed_response(response)
