"""
Unit tests for the `/role_permissions/roles/{role_id}` endpoint.

This module tests various scenarios for retrieving role information, ensuring proper
authorization, input validation, and response accuracy. It covers access for both
Super Admin and Regular User roles.

Test Scenarios:
1. **Unauthorized Access**:
    - No Authorization Token: Returns `401 Unauthorized` with "Could not validate credentials".
    - Invalid Authorization Token: Returns `401 Unauthorized` with "Could not validate credentials".
    - Missing Headers: Returns `401 Unauthorized` with "Not authenticated".

2. **Invalid Role ID**:
    - Missing `role_id`: Returns `400 Bad Request` with "Role Id must be required and valid."
    - Invalid `role_id` formats:
        - String-based invalid ObjectId.
        - Zero or negative integer.
      Each case returns `400 Bad Request` with the appropriate error message.

3. **Valid Role ID**:
    - **Super Admin**:
        - Successfully retrieves role information with `200 OK` status.
        - Ensures the response contains the required fields: `id`, `name`, `description`, and `permissions`.
    - **Regular User**:
        - Returns `401 Unauthorized` with "You are not authorized to perform this action!".

Parameters:
- http_client_test: Async HTTP client for making API requests.
- fetch_latest_role_perm: Fixture providing the latest created role object (for valid data tests).
- super_admin_token: Authorization token with Super Admin privileges.
- user_token: Authorization token with Regular User privileges.
- invalid_token: Simulates an invalid token scenario.

Test Coverage:
- Authorization checks (valid, invalid, missing).
- Input validation for `role_id`.
- Response structure and messages for different user roles.
- Successful data retrieval for valid requests.
"""

import pytest

from app.models.role_permission_schema import Roles
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_role_without_token(http_client_test):
    """
    Handles unit test for the `/roles/{role_id}` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/role_permissions/roles/1?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_role_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `/roles/{role_id}` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/role_permissions/roles/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_role_without_headers(http_client_test):
    """
    Handles a unit test for the `/roles/{role_id}` endpoint when called without headers.
    """
    response = await http_client_test.get(
        f"/role_permissions/roles/1?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Todo: Need to add updated testcases for get_role_details API.

#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "role_id, expected_status, expected_detail",
#     [
#         (
#             None,
#             400,
#             "Role Id must be required and valid.",
#         ),  # test `/roles/{role_id}` without role id.
#         (
#             "65f41ec543d505076037221",
#             400,
#             "Role Id must be required and valid.",
#             # test `/roles/{role_id}` with invalid role id, i.e. str
#         ),
#         (
#             0,
#             400,
#             "Role Id must be required and valid.",
#             # test `/roles/{role_id}` with invalid role id, i.e. 0.
#         ),
#         (
#             -2,
#             400,
#             "Role Id must be required and valid.",
#             # test `/roles/{role_id}` with invalid role id, i.e. negative
#         ),
#     ],
# )
# async def test_get_role(http_client_test, super_admin_token, user_token, role_id, expected_status, expected_detail):
#     """
#     Unit test for the `/roles/{role_id}` endpoint with Admin and User authorization tokens.
#
#     This test verifies that:
#     - Invalid or missing `role_id` returns a `400 Bad Request` response.
#     - Both Super Admin and Regular User receive the same error response for invalid `role_id`.
#
#     Parameters:
#     - http_client_test: Async HTTP client for sending requests.
#     - super_admin_token: Authorization token for a Super Admin.
#     - user_token: Authorization token for a Regular User.
#     - role_id: Input role ID being tested.
#     - expected_status: Expected HTTP status code.
#     - expected_detail: Expected error message in the response.
#
#     Assertions:
#     - Status code matches the expected value (`400` for invalid inputs).
#     - Error detail message matches the expected value:
#       - "Role Id must be required and valid." for invalid or missing `role_id`.
#
#     Test cases include:
#     1. Missing `role_id`.
#     2. Invalid `role_id` (string format).
#     3. Invalid `role_id` (zero or negative integer).
#     """
#
#     # testing with "super_admin_token"
#     response = await http_client_test.get(
#         f"/role_permissions/roles/{role_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing with "user_token"
#     response = await http_client_test.get(
#         f"/role_permissions/roles/{role_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Roles], indirect=True)
# async def test_get_role_with_valid_data(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `/roles/{role_id}` endpoint with valid data.
#
#     This test verifies that:
#     - A Super Admin can successfully fetch role details.
#     - A regular user is not authorized to access role information.
#
#     Parameters:
#     - http_client_test: Async HTTP client for sending requests.
#     - fetch_latest_role_perm: Fixture providing the most recently created role object.
#     - super_admin_token: Authorization token for a Super Admin.
#     - user_token: Authorization token for a regular user.
#
#     Assertions:
#     1. For a Super Admin:
#        - Status code is `200` (OK).
#        - The response message is "Role Fetched Successfully".
#        - The response contains the required fields: `id`, `name`, `description`, and `permissions`.
#
#     2. For a Regular User:
#        - Status code is `401` (Unauthorized).
#        - The error message is "You are not authorized to perform this action!".
#     """
#     role_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.get(
#         f"/role_permissions/roles/{role_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Role Fetched Successfully"
#     response_data = response.json()
#     assert all(
#         field_name in response_data.get("data", [])
#         for field_name in [
#             "id",
#             "name",
#             "description",
#             "permissions",
#         ]
#     )
#
#     # testing with "user_token"
#     response = await http_client_test.get(
#         f"/role_permissions/roles/{role_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
