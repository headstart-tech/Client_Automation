"""
Unit tests for the `/role_permissions/groups/{group_id}` endpoint.

This module tests various scenarios for retrieving group information, ensuring proper
authorization, input validation, and response accuracy. It covers access for both
Super Admin and Regular User roles.

Test Scenarios:
1. **Unauthorized Access**:
    - No Authorization Token: Returns `401 Unauthorized` with "Could not validate credentials".
    - Invalid Authorization Token: Returns `401 Unauthorized` with "Could not validate credentials".
    - Missing Headers: Returns `401 Unauthorized` with "Not authenticated".

2. **Invalid Group ID**:
    - Missing `group_id`: Returns `400 Bad Request` with "Group Id must be required and valid."
    - Invalid `group_id` formats:
        - String-based invalid ObjectId.
        - Zero or negative integer.
      Each case returns `400 Bad Request` with the appropriate error message.

3. **Valid Group ID**:
    - **Super Admin**:
        - Successfully retrieves group information with `200 OK` status.
        - Ensures the response contains the required fields: `id`, `name`, `description`, and `permissions`.
    - **Regular User**:
        - Returns `401 Unauthorized` with "You are not authorized to perform this action!".

Parameters:
- http_client_test: Async HTTP client for making API requests.
- fetch_latest_role_perm: Fixture providing the latest created group object (for valid data tests).
- super_admin_token: Authorization token with Super Admin privileges.
- user_token: Authorization token with Regular User privileges.
- invalid_token: Simulates an invalid token scenario.

Test Coverage:
- Authorization checks (valid, invalid, missing).
- Input validation for `group_id`.
- Response structure and messages for different user roles.
- Successful data retrieval for valid requests.
"""

import pytest

from app.models.role_permission_schema import Groups
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_group_without_token(http_client_test):
    """
    Handles unit test for the `/groups/{group_id}` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/role_permissions/groups/1?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_group_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `/groups/{group_id}` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/role_permissions/groups/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_group_without_headers(http_client_test):
    """
    Handles a unit test for the `/groups/{group_id}` endpoint when called without headers.
    """
    response = await http_client_test.get(
        f"/role_permissions/groups/1?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "group_id, expected_status, expected_detail",
    [
        (
            None,
            400,
            "Group Id must be required and valid.",
        ),  # test `/groups/{group_id}` without group id.
        (
            "65f41ec543d505076037221",
            400,
            "Group Id must be required and valid.",
            # test `/groups/{group_id}` with invalid group id, i.e. str
        ),
        (
            0,
            400,
            "Group Id must be required and valid.",
            # test `/groups/{group_id}` with invalid group id, i.e. 0.
        ),
        (
            -2,
            400,
            "Group Id must be required and valid.",
            # test `/groups/{group_id}` with invalid group id, i.e. negative
        ),
    ],
)
async def test_get_group(http_client_test, super_admin_token, user_token, group_id, expected_status, expected_detail):
    """
    Unit test for the `/groups/{group_id}` endpoint with Admin and User authorization tokens.

    This test verifies that:
    - Invalid or missing `group_id` returns a `400 Bad Request` response.
    - Both Super Admin and Regular User receive the same error response for invalid `group_id`.

    Parameters:
    - http_client_test: Async HTTP client for sending requests.
    - super_admin_token: Authorization token for a Super Admin.
    - user_token: Authorization token for a Regular User.
    - group_id: Input group ID being tested.
    - expected_status: Expected HTTP status code.
    - expected_detail: Expected error message in the response.

    Assertions:
    - Status code matches the expected value (`400` for invalid inputs).
    - Error detail message matches the expected value:
      - "Group Id must be required and valid." for invalid or missing `group_id`.

    Test cases include:
    1. Missing `group_id`.
    2. Invalid `group_id` (string format).
    3. Invalid `group_id` (zero or negative integer).
    """

    # testing with "super_admin_token"
    response = await http_client_test.get(
        f"/role_permissions/groups/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

    # testing with "user_token"
    response = await http_client_test.get(
        f"/role_permissions/groups/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

# TODO: Need to add updated testcases for get_group_details api.
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Groups], indirect=True)
# async def test_get_group_with_valid_data(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `/groups/{group_id}` endpoint with valid data.
#
#     This test verifies that:
#     - A Super Admin can successfully fetch group details.
#     - A regular user is not authorized to access group information.
#
#     Parameters:
#     - http_client_test: Async HTTP client for sending requests.
#     - fetch_latest_role_perm: Fixture providing the most recently created group object.
#     - super_admin_token: Authorization token for a Super Admin.
#     - user_token: Authorization token for a regular user.
#
#     Assertions:
#     1. For a Super Admin:
#        - Status code is `200` (OK).
#        - The response message is "Group Fetched Successfully".
#        - The response contains the required fields: `id`, `name`, `description`, and `permissions`.
#
#     2. For a Regular User:
#        - Status code is `401` (Unauthorized).
#        - The error message is "You are not authorized to perform this action!".
#     """
#     group_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.get(
#         f"/role_permissions/groups/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Group Fetched Successfully"
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
#         f"/role_permissions/groups/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
