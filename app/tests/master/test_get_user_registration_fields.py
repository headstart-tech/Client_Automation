"""
This module contains unit tests for the `get_user_registration_fields` endpoint in the Master's API.
The test cases cover various scenarios including:
- Testing the endpoint with different authorization tokens (valid, invalid, and missing).
- Testing the endpoint with different combinations of input parameters such as role_id.
- Verifying the response status codes and error messages.
Each test case is parametrized to cover multiple combinations of input parameters, such as:
- Valid, invalid and None role_id.
Additionally, there are separate test cases to verify the behavior when the request is made without an authorization
token, as well as when the request body is missing or invalid.
These tests ensure that the `get_user_registration_fields` endpoint behaves correctly under different conditions,
and that appropriate error messages are returned when necessary.
"""

import pytest

from app.models.role_permission_schema import Roles
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_user_registration_fields_without_token(http_client_test):
    """
    Handles unit test for the `get_user_registration_fields` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_user_registration_fields_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `get_user_registration_fields` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_user_registration_fields_without_headers(http_client_test):
    """
    Handles unit test for the `get_user_registration_fields` endpoint when called without request body.
    """

    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id=1&feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "role_id, expected_status, expected_detail",
    [
        (
            "65fc90aabf3ce46f00e28f8",
            400,
            "Role Id must be required and valid.",
        ),  # test get_user_registration_fields with invalid role_id
        (
            "role_id",
            400,
            "Role Id must be required and valid.",
        ),  # test get_user_registration_fields with invalid role_id
        (
            0,
            400,
            "Role Id must be required and valid.",
        ),  # test get_user_registration_fields with invalid role_id
        (
            -1,
            400,
            "Role Id must be required and valid.",
        ),  # test get_user_registration_fields with invalid role_id
        (
            False,
            400,
            "Role Id must be required and valid.",
        ),  # test get_user_registration_fields with invalid role_id
    ],
)
async def test_get_user_registration_fields_for_students(
    http_client_test,
    super_admin_token,
    access_token,
    role_id,
    expected_status,
    expected_detail,
):
    """
    Handles unit test for the `get_user_registration_fields` endpoint when called with super admin and student
    authorization token.
    """
    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id={role_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

    # testing with student token
    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id={role_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


@pytest.mark.asyncio
@pytest.mark.parametrize("fetch_latest_role_perm", [Roles], indirect=True)
async def test_get_user_registration_fields_with_valid_data(
    http_client_test,
    fetch_latest_role_perm,
    super_admin_token,
    access_token
):
    """
    Handles unit test for the `get_user_registration_fields` endpoint when called with valid data.
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().field_mapping_collection.delete_many({})
    value = {"field_name": "Your Full Name", "key_name": "full_name", "field_type": "text"}
    await DatabaseConfiguration().field_mapping_collection.insert_one(
        {"student_registration_form_fields": [value],"user_registration_common_fields": [value]})

    # testing with None role_id
    response = await http_client_test.get(
        f"/master/get_user_registration_fields?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Fields fetched successfully."

    role_id = fetch_latest_role_perm.id

    # testing with student token
    response = await http_client_test.get(
        f"/master/get_user_registration_fields?role_id={role_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
