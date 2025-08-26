"""
Unit tests for the `create_role` endpoint in the role_permissions module.

These tests validate the behavior of the endpoint when called with different user roles (super admin and regular user) and various request payloads.

Test Scenarios:

1. **Invalid Data Cases**
   - Ensure the endpoint returns a `400 Bad Request` for:
      - Invalid `name` type (non-string values)
      - Missing `name` field
      - Empty request body
   - Validate the correct error message is returned in the response.

2. **Valid Data Case**
   - Ensure a valid role creation request:
      - Returns `201 Created` with a success message when using a super admin token.
      - Contains the correct response structure with `name` and `description` fields.
      - Returns `401 Unauthorized` when a regular user attempts to create a role.

3. **Duplicate Data Case**
   - Ensure the endpoint prevents duplicate role names:
      - Returns `400 Bad Request` when attempting to create a role with an existing name.
      - Validate the correct error message for duplicate entries.
      - Ensure regular users cannot create roles (returns `401 Unauthorized`).

Parameters:
    http_client_test (AsyncClient): HTTP client for simulating requests.
    super_admin_token (str): Authorization token with super admin privileges.
    user_token (str): Authorization token with regular user privileges.
    user_request (dict): Payload for creating a role (name and description).
    expected_status (int): Expected HTTP status code.
    expected_detail (str): Expected error message in the response.
    fetch_latest_role_perm (Roles): Fixture to fetch the latest role from the database.

Usage:
    Run these tests with pytest and ensure the FastAPI application handles role creation accurately.

Example Command:
    pytest test_create_role.py --asyncio-mode=auto
"""

import time

import pytest

from app.models.role_permission_schema import Roles
from app.tests.conftest import user_token
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_role_without_token(http_client_test):
    """
    Handles unit test for the `create_role` endpoint when called with no authorization token.
    """
    response = await http_client_test.post(
        f"/role_permissions/create_role/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_create_role_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `create_role` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_role/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_create_role_without_headers(http_client_test):
    """
    Handles unit test for the `create_role` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_role/?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_role_without_request_body(http_client_test, super_admin_token):
    """
    Handles unit test for the `create_role` endpoint when called without request body.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_role/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=None,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."

# Todo: Need to add updated testcases for create_role

#
# @pytest.mark.parametrize(
#     "user_request, expected_status, expected_detail",
#     [
#         (
#             {
#                 "name": 121,
#                 "description": None,
#                 "scope": "None"
#             },
#             400,
#             "Value error, name must be a string",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": None,
#                 "description": None,
#                 "scope": None
#             },
#             400,
#             "Value error, name must be a string",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": "role",
#                 "description": None,
#                 "scope": None
#             },
#             400,
#             "Value error, Invalid scope value",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": "role",
#                 "description": None,
#                 "scope": "None"
#             },
#             400,
#             "Value error, Invalid scope value",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": "Role",
#                 "description": None,
#                 "scope": "Global"
#             },
#             400,
#             "Value error, Invalid scope value",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": "Role",
#                 "description": None,
#                 "scope": "scope"
#             },
#             400,
#             "Value error, Invalid scope value",
#         ),  # test create_role with invalid json
#         (
#             {
#                 "name": "Role",
#                 "description": None
#             },
#             400,
#             "Scope must be required and valid.",
#         ),  # test create_role with invalid json
#         (
#             None,
#             400,
#             "Body must be required and valid.",
#         ),  # test create_role with None json
#     ],
# )
# async def test_create_role_with_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Unit test for the `create_role` endpoint.
#
#     This test verifies the behavior of the `create_role` endpoint when provided with invalid input data.
#     It ensures that the system returns appropriate error messages and status codes when the request is invalid.
#
#     Parameters:
#     - http_client_test: HTTP client fixture for sending requests in the test environment.
#     - super_admin_token: Authorization token for a Super Admin user.
#     - user_token: Authorization token for a regular user.
#     - user_request: JSON payload sent in the request body.
#     - expected_status: Expected HTTP status code in the response.
#     - expected_detail: Expected error detail message in the response.
#
#     Test Scenarios:
#     1. Invalid 'name' field (integer instead of a string).
#     2. Missing 'name' field (None value).
#     3. Missing request body (None payload).
#
#     Assertions:
#     - Validates that the response status code matches `expected_status`.
#     - Checks that the `detail` field in the response matches `expected_detail` for errors.
#     - When a role is successfully created (status 201), ensures that required fields ('name', 'description') are present in the response.
#     """
#
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     if expected_status == 201:
#         assert response.json()["message"] == expected_detail
#         response_data = response.json()["data"]
#         assert all(
#             field_name in response_data
#             for field_name in [
#                 "name",
#                 "description",
#             ]
#         )
#     else:
#         assert response.json()["detail"] == expected_detail
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
#
# @pytest.mark.parametrize(
#     "user_request",
#     [
#         {
#             "name": f"role_{time.time()}",
#             "description": None,
#             "scope": "global"
#         },# test create_role with valid json,
#         {
#             "name": f"role_{time.time()}",
#             "description": None,
#             "scope": "college"
#         },# test create_role with valid json
#     ],
# )
# async def test_create_role_with_valid_data(
#     http_client_test,
#     user_token,
#     super_admin_token,
#     user_request,
# ):
#     """
#     Unit test for the `create_role` endpoint with valid input data.
#
#     This test verifies the behavior of the `create_role` endpoint when provided with valid input data.
#     It ensures that a Super Admin can successfully create a role, while a regular user is unauthorized.
#
#     Parameters:
#     - http_client_test: HTTP client fixture for sending requests in the test environment.
#     - super_admin_token: Authorization token for a Super Admin user.
#     - user_token: Authorization token for a regular user.
#     - user_request: JSON payload sent in the request body.
#
#     Test Scenarios:
#     1. Valid role creation by a Super Admin.
#     2. Unauthorized role creation attempt by a regular user.
#
#     Assertions:
#     - Validates that the response status code is 201 when a Super Admin creates a role.
#     - Checks that the `message` field confirms successful creation.
#     - Ensures required fields ('name', 'description') are present in the response.
#     - Validates that a regular user receives a 401 Unauthorized response.
#     """
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == 201
#     assert response.json()["message"] == "Role created successfully."
#     response_data = response.json()["data"]
#     for field_name in [
#         "name",
#         "description",
#         "scope",
#         "created_at"
#     ]:
#         assert field_name in response_data
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Roles], indirect=True)
# async def test_create_role_with_duplicate_data(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `create_role` endpoint to handle duplicate role creation attempts.
#
#     This test verifies:
#     1. If a super admin attempts to create a role with a duplicate name, the API returns a 400 status code with an appropriate error message.
#     2. If a regular user without proper authorization attempts to create a role, the API returns a 401 status code with an "unauthorized" error message.
#
#     Parameters:
#     - http_client_test: Async HTTP client for making API requests.
#     - fetch_latest_role_perm: Fixture to fetch the latest role from the database.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#
#     Assertions:
#     - Ensure a 400 response with a "Role already exists" error for duplicate role creation by a super admin.
#     - Ensure a 401 response with an "unauthorized" error for role creation by a regular user.
#     """
#     duplicate_name = fetch_latest_role_perm.name
#     json_obj = {
#         "name": duplicate_name,
#         "description": "Testing duplicate insertion."
#     }
#
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         "/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == f"Role already exists with name '{duplicate_name}'."
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         "/role_permissions/create_role/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
