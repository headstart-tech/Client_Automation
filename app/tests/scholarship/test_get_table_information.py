"""
This file contains test cases of get scholarship table information API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_scholarship_table_information(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation, test_create_scholarship_data):
    """
    Different test cases of get scholarship table information.

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
        test_create_scholarship_data: A fixture which return dummy scholarship data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for get scholarship table information.
    response = await http_client_test.post(f"/scholarship/table_information/?college_id={college_id}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required page number for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Num must be required and valid.'}

    # Required page size for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Page Size must be required and valid.'}

    # No permission for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    async def validate_custom_scholarship_info(temp_response, invalid_response=False):
        assert "custom_scholarship_info" in temp_response.json()
        for field_name in ["_id", "name", "offered_applicants_count", "availed_applicants_count", "availed_amount",
                           "status"]:
            assert field_name in temp_response.json()["custom_scholarship_info"]
            if field_name == "name":
                assert temp_response.json()["custom_scholarship_info"]["name"] == "Custom scholarship"
            if field_name == "status":
                assert temp_response.json()["custom_scholarship_info"]["status"] == "Active"
            if field_name == "_id":
                assert temp_response.json()["custom_scholarship_info"]["_id"] == "None"
            if invalid_response and field_name in ["offered_applicants_count", "availed_applicants_count", "availed_amount"]:
                assert temp_response.json()["custom_scholarship_info"][field_name] == 0

    async def validate_common_response(temp_response):
        assert temp_response.status_code == 200
        assert temp_response.json()['message'] == "Get scholarship table information."

    # Get scholarship table information.
    async def validate_successful_response(temp_response):
        await validate_common_response(temp_response)
        temp_data = temp_response.json()["data"][0]
        for field_name in ["_id", "name", "programs", "count", "offered_applicants_count", "availed_applicants_count",
                           "available", "availed_amount", "status"]:
            assert field_name in temp_data
            for field_name1 in ["name", "status", "_id"]:
                assert temp_data[field_name1] == str(test_scholarship_validation.get(field_name1))
        await validate_custom_scholarship_info(temp_response)

    # Get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_successful_response(response)

    # Get scholarship table information by search.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": "test"}
    )
    await validate_successful_response(response)

    # Get scholarship table information by sort.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "asc"}
    )
    await validate_successful_response(response)

    # Get scholarship table information by programs.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_successful_response(response)

    # Invalid college id for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id=123&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id=123456789012345678901234&page_num=1&page_size=6"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    async def validate_failed_response(temp_response):
        await validate_common_response(temp_response)
        assert response.json()['data'] == []
        await validate_custom_scholarship_info(response, invalid_response=True)

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scholarship_collection.delete_many({})
    # Scholarship data not found when get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    await validate_failed_response(response)

    # Scholarship data not found when get scholarship table information by search.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search": "test"}
    )
    await validate_failed_response(response)

    # Scholarship data not found when get scholarship table information by sort.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "asc"}
    )
    await validate_failed_response(response)

    # Scholarship data not found when get scholarship table information by programs.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"programs": test_create_scholarship_data.get("programs")}
    )
    await validate_failed_response(response)

    # Invalid sort type when get scholarship table information.
    response = await http_client_test.post(
        f"/scholarship/table_information/?college_id={college_id}&page_num=1&page_size=6&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"sort": "name", "sort_type": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Sort Type must be required and valid.'}
