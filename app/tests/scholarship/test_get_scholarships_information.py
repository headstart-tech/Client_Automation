"""
This file contains test cases of get scholarships information API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_scholarships_information(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation):
    """
    Different test cases of get scholarships information.

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

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for get scholarships information.
    response = await http_client_test.get(f"/scholarships/get_information/?college_id={college_id}"
                                          f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    def validate_successful_response(temp_response):
        assert temp_response.json()['message'] == "Get scholarships information."
        for field_name in ["name", "count", "waiver_type", "waiver_value", "status", "_id", "programs"]:
            temp_data = temp_response.json()["data"][0]
            assert field_name in temp_data
            if field_name not in ["_id", "copy_scholarship_id", "template_id", "programs"]:
                assert temp_data[field_name] == test_scholarship_validation.get(field_name)
            if field_name in ["_id", "copy_scholarship_id", "template_id"]:
                assert temp_data[field_name] in str(test_scholarship_validation.get(field_name))

    # Get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    validate_successful_response(response)

    # Get scholarships information by scholarship_id.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}"
        f"&scholarship_id={str(test_scholarship_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    validate_successful_response(response)

    # Invalid scholarship id for get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}&scholarship_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Scholarship id `123` must be a 12-byte input or a 24-character hex string"

    # Invalid college id for get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    def validate_no_data_response(temp_response):
        assert temp_response.status_code == 200
        assert temp_response.json()['message'] == "Get scholarships information."
        assert temp_response.json()['data'] == []

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scholarship_collection.delete_many({})
    # Scholarship not found when get scholarships information.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    validate_no_data_response(response)

    # Scholarship information not found by scholarship id.
    response = await http_client_test.get(
        f"/scholarships/get_information/?college_id={college_id}"
        f"&scholarship_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    validate_no_data_response(response)
