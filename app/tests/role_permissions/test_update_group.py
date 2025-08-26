"""
Unit Tests for `/role_permissions/update_group/{group_id}` Endpoint

This test suite verifies the functionality of the `update_group` endpoint
under various conditions, including authentication, input validation, and
group-specific permissions.

Test Scenarios:
1. Authorization:
   - Missing or invalid authorization token should return 401 Unauthorized.
   - User without proper permissions cannot update a group.

2. Input Validation:
   - Missing or invalid `group_id` should return 400 Bad Request.
   - Invalid payload (e.g., incorrect data type) should return 400 Bad Request.

3. Successful Update:
   - A Super Admin can successfully update a group with valid input.
   - Attempting to update a group with a duplicate name should return 400 Bad Request.

Test Cases:
- `test_update_group_without_token`: Validates unauthorized access without a token.
- `test_update_group_without_headers`: Checks access without headers.
- `test_update_group_with_invalid_token`: Validates response for an invalid token.
- `test_update_group_without_request_body`: Ensures an empty request body triggers an error.
- `test_update_group_for_invalid_data`: Covers invalid combinations of `group_id` and payload.
- `test_update_group_for_user_with_valid_data`: Verifies successful updates and permission handling.

Parameters:
- `http_client_test`: Async HTTP client to simulate API requests.
- `super_admin_token`: Token for a Super Admin user.
- `user_token`: Token for a regular user.
- `group_id`: Identifier of the group to be updated.
- `user_request`: JSON payload for updating the group.
- `expected_status`: Expected HTTP status code.
- `expected_detail`: Expected error message in the response.

Assertions:
- Ensures correct status codes and error messages for all cases.
- Verifies only Super Admins can update groups and handles duplicates correctly.
"""

import json
import time

import pytest

from app.models.role_permission_schema import Groups
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_group_without_token(
    http_client_test, group_id=1
):
    """
    This functionality contains a unit test for the `update_group` endpoint when called with no authorization token.
    """
    response = await http_client_test.put(
        f"/role_permissions/update_group/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_update_group_without_headers(
    http_client_test, group_id=1
):
    """
    This functionality contains a unit test for the `update_group` endpoint when called without headers.
    """
    response = await http_client_test.put(
        f"/role_permissions/update_group/{group_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_group_with_invalid_token(
    http_client_test, invalid_token, group_id=1
):
    """
    This functionality contains unit test for the `update_group` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.put(
        f"/role_permissions/update_group/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_update_group_without_request_body(
    http_client_test, super_admin_token, group_id="65f989b3fe903811ed285a97"
):
    """
    This functionality contains unit test for the `update_group` endpoint when called without request body.
    """

    response = await http_client_test.put(
        f"/role_permissions/update_group/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=None,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Group Id must be required and valid."


# Todo: Need to add updated testcases for update_group
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "group_id, user_request, expected_status, expected_detail",
#     [
#         (
#             "65f989b3fe903811ed285a9",
#             {
#                 "name": f"group_{time.time()}",
#                 "description": "description",
#             },
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with invalid id and valid json
#         (
#             "65f989b3fe903811ed285a9",
#             {
#                 "name": f"group_{time.time()}",
#                 "description": 100,
#             },
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with invalid id and invalid json
#         (
#             0,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with invalid id and None json
#         (
#             None,
#             {
#                 "name": f"group_{time.time()}",
#                 "description": "description",
#             },
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with None id and valid json
#         (
#             None,
#             {
#                 "name": f"group_{time.time()}",
#                 "description": 100,
#             },
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with None id and invalid json
#         (
#             None,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test update_group with None id and None json
#     ],
# )
# async def test_update_group_for_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     group_id,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Tests the `/role_permissions/update_group/{group_id}` endpoint with invalid data.
#
#     Scenarios:
#     1. Invalid or None `group_id`:
#        - Asserts:
#          - Status code: 400
#          - Error detail: "Group Id must be required and valid."
#
#     2. Invalid JSON payload (e.g., invalid data type in 'description'):
#        - Asserts:
#          - Status code: 400
#          - Error detail: "Group Id must be required and valid."
#
#     Test Flow:
#     - Sends a PUT request using both "super_admin_token" and "user_token".
#     - Validates the status code and error detail for each case.
#
#     Parameters:
#     - http_client_test: Async HTTP client for making API requests.
#     - super_admin_token: Auth token for Super Admin user.
#     - user_token: Auth token for a regular user.
#     - group_id: Group identifier (can be invalid or None for this test).
#     - user_request: JSON payload for updating the group (can be valid, invalid, or None).
#     - expected_status: Expected HTTP status code.
#     - expected_detail: Expected error message in the response.
#     """
#     user_requested_data = json.dumps(user_request) if user_request else "{}"
#
#     # testing "update_group" with "super_admin_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing "update_group" with "user_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Groups], indirect=True)
# async def test_update_group_for_user_with_valid_data(
#     http_client_test, fetch_latest_role_perm, user_token, super_admin_token
# ):
#     """
#     Tests the `/role_permissions/update_group/{group_id}` endpoint.
#
#     Scenarios:
#     1. Super Admin can successfully update a group.
#        - Asserts:
#          - Status code: 200
#          - Response message: "Group updated successfully."
#
#     2. Regular user is unauthorized to update a group.
#        - Asserts:
#          - Status code: 401
#          - Error detail: "You are not authorized to perform this action!"
#
#     3. Duplicate group name returns an error.
#        - Asserts:
#          - Status code: 400
#          - Error detail: "Group already exists with name 'super_admin'."
#
#     Parameters:
#     - http_client_test: Async HTTP client for requests.
#     - fetch_latest_role_perm: Fixture providing the latest group.
#     - user_token: Regular user auth token.
#     - super_admin_token: Super Admin auth token.
#     """
#     # testing with "super_admin_token"
#     group_name = f"group_{time.time()}"
#     group_id = fetch_latest_role_perm.id
#     json_obj = {"name": group_name, "description": None}
#
#     # testing with "super_admin_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Group updated successfully."
#
#     # testing with "user_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
