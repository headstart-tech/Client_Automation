"""
This file contains test cases related to get course specialization (s) list
course.
"""
import pytest


@pytest.mark.asyncio
async def test_get_course_specializations(
        http_client_test, test_college_validation, test_course_validation,
        college_super_admin_access_token, access_token, setup_module):
    """
    Test cases related to get course specialization (s) list.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_course_validation: A fixture which create course data if
            not exist and return course data.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - access_token: A fixture which create student if not exist
            and return access token for student.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.

    Assertions:
        response status code and json message.
    """

    # Required college id when get course specialization (s) list.
    response = await http_client_test.get("/course/specialization_list/")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "College Id must be required and valid."}

    # Invalid college id when get course specialization (s) list.
    response = await http_client_test.get(
        "/course/specialization_list/?college_id=1234"
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": 'College id must be a 12-byte input or a 24-character '
                      'hex string'}

    # College not found when get course specialization (s) list.
    response = await http_client_test.get(
        "/course/specialization_list/?college_id=123456789012345678901234"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    college_id = str(test_college_validation.get('_id'))
    # Required course information when get course specialization (s) list.
    response = await http_client_test.get(
        f"/course/specialization_list/?"
        f"college_id={college_id}"
    )
    assert response.status_code == 400
    assert response.json() == \
           {'detail': "Course id or name must be required to get course "
                      "specialization (s) information."}

    # Course not found by course name when get course specialization (s) list.
    response = await http_client_test.get(
        f"/course/specialization_list/?college_id={college_id}&course_name"
        f"=wrong_name"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"

    # Course not found by course id when get course specialization (s) list.
    response = await http_client_test.get(
        f"/course/specialization_list/?college_id={college_id}&course_id=123456789012345678901234"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"

    # Invalid course id when get course specialization (s) list.
    response = await http_client_test.get(
        f"/course/specialization_list/?"
        f"college_id={college_id}&course_id=123"
    )
    assert response.status_code == 422
    assert response.json() == {"detail": 'Course id `123` must be a 12-byte '
                                         'input or a 24-character hex string'}

    def validate_successful_response(valid_response):
        """
        Validate successful response of test case.
        """
        assert valid_response.status_code == 200
        data = valid_response.json()
        assert (
                data["message"]
                == "Course specializations data fetched successfully."
        )
        for item in ["college_id", "course_id", "course_specialization",
                     "fees", "is_activated", "banner_image_url"]:
            assert item in data["data"][0][0]

    # Get course specialization list by course name.
    response = await http_client_test.get(
        f"/course/specialization_list/?college_id={str(test_course_validation.get('college_id'))}&course_name={test_course_validation.get('course_name')}"
    )
    validate_successful_response(response)

    # Get course specialization list by course id.
    response = await http_client_test.get(
        f"/course/specialization_list/?college_id={str(test_course_validation.get('college_id'))}&course_id={str(test_course_validation.get('_id'))}"
    )
    validate_successful_response(response)
