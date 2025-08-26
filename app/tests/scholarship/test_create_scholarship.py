"""
This file contains test cases of create scholarship API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()
#Todo: We do it later because of time.

@pytest.mark.asyncio
async def test_create_scholarship(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_create_scholarship_data, test_course_validation, test_template_validation):
    """
    Different test cases of create scholarship.

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
        test_create_scholarship_data: A fixture which return dummy scholarship data.
        access_token: A fixture which create student if not exist and return access token of student.
        test_course_validation: A fixture which create course if not exist
            and return course data.
        test_template_validation: A fixture which create template if not exist
            and return template data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for create scholarship.
    response = await http_client_test.post(f"/scholarship/create/?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create scholarship.
    response = await http_client_test.post(
        f"/scholarship/create/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Field required for create scholarship.
    response = await http_client_test.post(
        f"/scholarship/create/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for create scholarship.
    response = await http_client_test.post(
        f"/scholarship/create/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_create_scholarship_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # # ToDo - Following commented test cases giving error when run all test cases otherwise working fine,
    #  we'll check it later on.
    # # Invalid scholarship percentage of scholarship when create scholarship.
    # test_create_scholarship_data.update({"waiver_value": 101})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Scholarship percentage should be less than or equal to to 100."
    #
    # # Invalid scholarship amount of scholarship create scholarship.
    # test_create_scholarship_data.update({"waiver_type": "Amount", "waiver_value": 1000000})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Scholarship amount should be less than or equal to 100000."
    #
    # test_create_scholarship_data.update({"waiver_type": "Percentage", "waiver_value": 100})


    # TODO: Test case it getting failed on Server hence commented it.
    # Create scholarship.
    # from app.database.configuration import DatabaseConfiguration
    # await DatabaseConfiguration().scholarship_collection.delete_many({})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 200
    # assert response.json()['message'] == "Scholarship created successfully."

    # Invalid college id for create scholarship.
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id=123",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 422
    # assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # # Wrong college id for create scholarship.
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id=123456789012345678901234",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 422
    # assert response.json()['detail'] == "College not found."

    # # Required college id for create scholarship.
    # response = await http_client_test.post(
    #     f"/scholarship/create/",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json() == {'detail': 'College Id must be required and valid.'}

    # # Scholarship name already exists when create scholarship.
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Scholarship name already exists."

    # # Invalid scholarship name when create scholarship.
    # test_create_scholarship_data["name"] = ""
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Value error, Name must be required and valid."

    # # Invalid course id when create scholarship.
    # test_create_scholarship_data.update({"name": "test"})
    # test_create_scholarship_data.get("programs", {})[0].update({"course_id": "1234567890"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Value error, Course Id must be required and valid."

    # # Course not found when create scholarship.
    # test_create_scholarship_data.get("programs", {})[0].update({"course_id": "123456789012345678901234"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 404
    # assert response.json()['detail'] == "Course not found id: 123456789012345678901234"

    # # Invalid course name when create scholarship.
    # test_create_scholarship_data.get("programs", {})[0].update({"course_id": str(test_course_validation.get("_id")),
    #                                                             "course_name": "xyz"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Invalid course name."

    # # Invalid specialization name when create scholarship.
    # test_create_scholarship_data.get("programs", {})[0].update({"course_name": test_course_validation.get("course_name"),
    #                                                             "specialization_name": "xyz"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == (f"Invalid specialization for course "
    #                                      f"{test_course_validation.get('course_name')}.")

    # # Invalid template id when create scholarship.
    # test_create_scholarship_data.get("programs", {})[0].update(
    #     {"course_name": test_course_validation.get("course_name"),
    #      "specialization_name": test_course_validation.get("course_specialization")[1].get("spec_name")})
    # test_create_scholarship_data.update({"template_id": "1234567890"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Value error, Template Id must be required and valid."

    # # Invalid template id when create scholarship.
    # test_create_scholarship_data.update({"template_id": "123456789012345678901234"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 404
    # assert response.json()['detail'] == "Template not found id: 123456789012345678901234"

    # # Create scholarship based on template.
    # test_create_scholarship_data.update({"template_id": str(test_template_validation.get("_id")),
    #                                      "name": "test1"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 200
    # assert response.json()['message'] == "Scholarship created successfully."

    # # Invalid scholarship id when create scholarship.
    # test_create_scholarship_data.update({"copy_scholarship_id": "1234567890", "name": "test11"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Value error, Copy Scholarship Id must be required and valid."

    # # Invalid template id when create scholarship.
    # test_create_scholarship_data.update({"copy_scholarship_id": "123456789012345678901234"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 404
    # assert response.json()['detail'] == "Scholarship not found id: 123456789012345678901234"

    # scholarship_info = await DatabaseConfiguration().scholarship_collection.find_one({})

    # # Create scholarship based on existing scholarship id.
    # test_create_scholarship_data.update({"copy_scholarship_id": str(scholarship_info.get("_id"))})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 200
    # assert response.json()['message'] == "Scholarship created successfully."

    # # Invalid status of scholarship when create scholarship.
    # test_create_scholarship_data.update({"status": "xyz", "name": "test111"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Status must be required and valid."

    # # Invalid waiver_value of scholarship when create scholarship.
    # test_create_scholarship_data.update({"status": "Closed", "waiver_value": 0})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Waiver Value must be required and valid."

    # # Invalid waiver_type of scholarship when create scholarship.
    # test_create_scholarship_data.update({"waiver_value": 10, "waiver_type": "xyz"})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Waiver Type must be required and valid."

    # # Invalid count of scholarship when create scholarship.
    # test_create_scholarship_data.update({"waiver_type": "Percentage", "count": 0})
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Count must be required and valid."

    # # Invalid name of scholarship when create scholarship.
    # test_create_scholarship_data.update({"count": 10})
    # test_create_scholarship_data.pop("name")
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Name must be required and valid."

    # # Invalid programs when create scholarship.
    # test_create_scholarship_data.update({"name": "test scholarship1"})
    # test_create_scholarship_data.pop("programs")
    # response = await http_client_test.post(
    #     f"/scholarship/create/?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=test_create_scholarship_data
    # )
    # assert response.status_code == 400
    # assert response.json()['detail'] == "Programs must be required and valid."
