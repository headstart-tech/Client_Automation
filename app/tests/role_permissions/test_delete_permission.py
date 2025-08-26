"""
Unit tests for the `delete_permission` endpoint in the role_permissions API.

This test file covers various test cases for the deletion of roles in the system, including:

1. Deleting a permission without providing an authorization token.
2. Deleting a permission with an invalid authorization token.
3. Deleting roles with invalid or non-existent permission IDs.
4. Verifying that both 'admin' and 'user' roles can successfully delete roles.

Test scenarios:
- `test_delete_permission_with_no_token`: Ensures the request is unauthorized without a token.
- `test_delete_permission_with_invalid_token`: Ensures the request is unauthorized with an invalid token.
- `test_delete_permission_for_invalid_ids`: Tests the deletion of roles with invalid IDs (invalid format, missing,
    or non-existent).
- `test_delete_permission_for_invalid_ids`: Verifies the ability of an admin/user to delete a permission.
- `test_delete_permission_for_valid_ids`: Verifies the ability of a admin/user to delete a permission.
"""

import pytest

from app.models.role_permission_schema import Permission
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_permission_with_no_token(
    http_client_test, perm_id=1
):
    """
    Handles a unit test for the `delete_permission` endpoint when called with no token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_permission/{perm_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_delete_permission_without_headers(
    http_client_test, perm_id=1
):
    """
    Handles a unit test for the `delete_permission` endpoint when called without headers.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_permission/{perm_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_permission_with_invalid_token(
    http_client_test,
    invalid_token,
    perm_id=1,
):
    """
    Handles a unit test for the `delete_permission` endpoint when called with an invalid token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_permission/{perm_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# Todo: Need to add updated testcases for delete_permission
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "perm_id, expected_status, expected_detail",
#     [
#         (
#             "65fad4822419830213cc4818",
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test delete_permission with invalid perm_id
#         (
#             None,
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test delete_permission with no perm_id
#         (
#             0,
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test delete_permission with invalid perm_id i.e. 0
#         (
#             -1,
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test delete_permission with invalid perm_id i.e. negative
#     ],
# )
# async def test_delete_permission_for_invalid_ids(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     perm_id,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Unit test for the `delete_permission` endpoint to validate error handling for invalid permission IDs.
#
#     This test ensures that invalid `perm_id` values trigger appropriate error responses when attempting to
#     delete a permission. The test is executed with both a super admin token (authorized) and a user token (unauthorized).
#
#     Test Scenarios:
#     1. Invalid ObjectId format (e.g., incorrect length or non-hexadecimal characters).
#     2. Missing `perm_id` (None).
#     3. Non-sensical values (e.g., `0`, `-1`).
#
#     Parameters:
#     - http_client_test: Async HTTP client for sending requests.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#     - perm_id: The permission ID being tested.
#     - expected_status: The expected HTTP status code for the response.
#     - expected_detail: The expected error message in the response.
#
#     Assertions:
#     - Ensure a 400 Bad Request response is returned for invalid `perm_id` values.
#     - Verify the correct error message is provided in the "detail" field.
#     - Ensure the behavior is consistent for both super admin and regular user tokens.
#     """
#
#     # testing with 'admin_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_permission/{perm_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing with 'user_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_permission/{perm_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Permission], indirect=True)
# async def test_delete_permission_for_valid_id(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `delete_permission` endpoint to validate successful deletion and error handling.
#
#     This test verifies the following scenarios:
#     1. A super admin can successfully delete a valid permission.
#     2. Attempting to delete the same permission again returns a 404 error indicating it no longer exists.
#     3. A regular user without appropriate permissions receives a 401 Unauthorized response.
#
#     Parameters:
#     - http_client_test: Async HTTP client for sending API requests.
#     - fetch_latest_role_perm: Fixture to fetch the latest permission from the database.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#
#     Test Cases:
#     1. Valid permission deletion:
#        - Expect a 200 status code with the message "Permission deleted successfully."
#     2. Deleting a non-existent permission:
#        - Expect a 404 status code with the message "Permission with id '{perm_id}' doesn't exist."
#     3. Unauthorized deletion attempt by a regular user:
#        - Expect a 401 status code with the message "You are not authorized to perform this action!"
#
#     Assertions:
#     - Successful deletion returns a 200 status code and appropriate success message.
#     - Repeated deletion attempts return a 404 status code and appropriate error message.
#     - Unauthorized user deletion attempts return a 401 status code and appropriate error message.
#     """
#     perm_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_permission/{perm_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Permission deleted successfully."
#
#     # testing with "super_admin_token" for non-existential data
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_permission/{perm_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == f"Permission with id '{perm_id}' doesn't exist."
#
#     # testing with "user_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_permission/{perm_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
