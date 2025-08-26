"""
This module contains unit tests for the `application_tabs` endpoint in the college API.

The test cases cover various scenarios including:
- Testing the endpoint with different authorization tokens (valid, invalid, and missing).
- Testing the endpoint with different combinations of input parameters such as college_id, course_id, and step_id.
- Verifying the response status codes and error messages.

The tests are organized into two main groups:
1. Tests for students.

Each test case is parametrized to cover multiple combinations of input parameters, such as:
- Valid and invalid college_id.
- Valid and invalid course_id.
- Valid and invalid step_id.
- None values for college_id, course_id, and step_id.

Additionally, there are separate test cases to verify the behavior when the request is made without an authorization
token, as well as when the request body is missing or invalid.

These tests ensure that the `application_tabs` endpoint behaves correctly under different conditions,
and that appropriate error messages are returned when necessary.
"""

import pytest

from app.tests.conftest import access_token, user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_application_tabs_without_token(
    http_client_test, college_id="65f989b3fe903811ed285a97"
):
    """
    Handles unit test for the `application_tabs` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/college/application_tabs/{college_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_application_tabs_with_invalid_token(
    http_client_test,
    invalid_token,
    college_id="65f989b3fe903811ed285a97",
):
    """
    Handles unit test for the `application_tabs` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/college/application_tabs/{college_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_application_tabs_without_headers(
    http_client_test,
    college_id="65f989b3fe903811ed285a97",
):
    """
    Handles unit test for the `application_tabs` endpoint when called without request body.
    """

    response = await http_client_test.get(
        f"/college/application_tabs/{college_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "college_id, course_id, step_id, expected_status, expected_detail",
    [
        (
            "65fc90aabf3ce46f00e28f8",
            "65fc90aabf3ce46f00e28f8",
            "e6jw790k",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with invalid id, valid course_id and valid step_id
        (
            "65fc90aabf3ce46f00e28f8de", # length > 24
            "65fc90aabf3ce46f00e28f8",
            "string",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with invalid id, valid course_id and invalid step_id
        (
            None,
            "e6jw790k",
            "65fc90aabf3ce46f00e28f8",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, valid course_id and valid step_id
        (
            None,
            "65fc90aabf3ce46f00e28f8",
            "step_id",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, valid course_id and invalid step_id
        (
            None,
            "65fc90aabf3ce46f00e28f8",
            None,
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, valid course_id and None step_id
        (
            "6800c8a3a65519d7648fb160",
            "65fc90aabf3ce46f00e28f8",  # length < 24
            "e6jw790k",
            404,
            "College not found",
        ),  # test application_tabs with invalid id, invalid course_id and valid step_id
        (
            "6800c8a3a65519d7648fb160",
            "65fc90aabf3ce46f00e28f8d",
            "testing",
            404,
            "College not found",
        ),  # test application_tabs with invalid id, invalid course_id and invalid step_id
        (
            "65fc90aabf3ce46f00e28f8di", # length > 24
            "course_id",
            None,
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with invalid id, invalid course_id and None step_id
        (
            None,
            1265,
            "e6jw790k",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, invalid course_id and valid step_id
        (
            None,
            "e6jw790k",
            {},
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, invalid course_id and invalid step_id
        (
            None,
            "e6jw790k",
            None,
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, invalid course_id and None step_id
        (
            "65fc90aabf3ce46f00e28f7d",
            None,
            "e6jw790k101",
            404,
            "College not found",
        ),  # test application_tabs with invalid id, None course_id and invalid step_id
        (
            None,
            None,
            "e6jw790k",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, None course_id and valid step_id
        (
            None,
            None,
            "e6jw790k202",
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, None course_id and invalid step_id
        (
            None,
            None,
            None,
            422,
            "College Id must be a 12-byte input or a 24-character hex string",
        ),  # test application_tabs with None id, None course_id and None step_id
    ],
)
async def test_application_tabs_for_students(
    http_client_test,
    access_token,
    college_id,
    course_id,
    step_id,
    expected_status,
    expected_detail,
):
    """
    Handles unit test for the `application_tabs` endpoint when called with student authorization token.
    """
    response = await http_client_test.get(
        f"/college/application_tabs/{college_id}?course_id={course_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

# TODO: API got updated by suphiya, need to update the testcase

# async def test_application_tabs_with_valid_data(
#     http_client_test,
#     test_application_form,
#     access_token,
# ):
#     """
#     Handles unit test for the `application_tabs` endpoint when called with valid data.
#     """
#     college_id = test_application_form.get("college_id")
#     course_id = test_application_form.get("course_id")
#     step_id = test_application_form.get("application_form", [])[0].get("step_id")
#     response = await http_client_test.get(
#         f"/college/application_tabs/{college_id}?course_id={course_id}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Application stages fetched successfully."
#
#     # testing with valid college_id, None course_id and invalid step_id
#     response = await http_client_test.get(
#         f"/college/application_tabs/{college_id}?step_id=step_id&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == ("No form data found for Step step_id in the application form. "
#                                          "Please verify the Step ID.")
#
#     # testing with valid college_id, invalid course_id and invalid step_id
#     response = await http_client_test.get(
#         f"/college/application_tabs/{college_id}?course_id=65fc90aabf3ce46f00e28f7d"
#         f"&step_id=step_id&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == ("No form data found for Step step_id in the application form. "
#                                          "Please verify the Step ID.")
#
#     # testing with valid step_id
#     response = await http_client_test.get(
#         f"/college/application_tabs/{college_id}?course_id={course_id}&step_id={step_id}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Stage data fetched successfully."
