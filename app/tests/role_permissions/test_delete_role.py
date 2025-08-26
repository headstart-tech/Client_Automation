"""
Unit Tests for the `delete_role` Endpoint

This module contains asynchronous pytest tests to validate the behavior of the `delete_role` endpoint.
The tests cover various scenarios including valid and invalid role deletion, authentication checks,
and permission enforcement.

Tested Endpoint:
    DELETE /role_permissions/delete_role/{role_id}

Fixtures:
    - http_client_test: Provides an asynchronous HTTP client for testing.
    - fetch_latest_role_perm: Fixture to fetch the most recently created role object.
    - super_admin_token: Provides a valid token for a Super Admin user.
    - user_token: Provides a valid token for a regular user.
    - invalid_token: Provides an invalid token for testing.

Test Scenarios:
    1. Unauthorized Access:
       - No token provided.
       - Missing authorization headers.
       - Invalid token usage.

    2. Invalid Role ID:
       - Non-existent role ID.
       - Improperly formatted ObjectId.
       - `None` as role ID.
       - Zero or negative role ID values.

    3. Valid Role Deletion:
       - Super Admin can delete a valid role successfully.
       - Deleting a non-existent role returns a 400 error.
       - Regular users without proper permissions cannot delete roles (401 Unauthorized).

Assertions:
    - HTTP status codes (200, 400, 401) are checked for correctness.
    - Appropriate error messages are validated for each scenario.
    - Access control is enforced between Super Admins and regular users.
"""

import pytest

from app.models.role_permission_schema import Roles
from app.tests.conftest import user_token
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_role_with_no_token(
    http_client_test, role_id=1
):
    """
    Handles a unit test for the `delete_role` endpoint when called with no token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_role/{role_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_delete_role_without_headers(
    http_client_test, role_id=1
):
    """
    Handles a unit test for the `delete_role` endpoint when called without headers.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_role/{role_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_role_with_invalid_token(
    http_client_test,
    invalid_token,
    role_id=1,
):
    """
    Handles a unit test for the `delete_role` endpoint when called with an invalid token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_role/{role_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# Todo: Need to add updated testcases for delete_role
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "role_id, expected_status, expected_detail",
#     [
#         (
#             "65fad4822419830213cc4818",
#             400,
#             "Role Id must be required and valid.",
#         ),  # test delete_role with invalid role_id
#         (
#             None,
#             400,
#             "Role Id must be required and valid.",
#         ),  # test delete_role with no role_id
#         (
#             0,
#             400,
#             "Role Id must be required and valid.",
#         ),  # test delete_role with invalid role_id i.e. 0
#         (
#             -1,
#             400,
#             "Role Id must be required and valid.",
#         ),  # test delete_role with invalid role_id i.e. negative
#     ],
# )
# async def test_delete_role_for_invalid_ids(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     role_id,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Unit test for the `delete_role` endpoint to validate handling of invalid role IDs.
#
#     This test ensures that the system correctly responds to invalid role identifiers when attempting to delete a role.
#     It checks the behavior for different invalid `role_id` values, including:
#     - An improperly formatted ObjectId.
#     - A `None` value (missing role ID).
#     - Zero or negative values.
#
#     Parameters:
#     - http_client_test: Async HTTP client used for sending API requests.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#     - role_id: The role ID to be tested (invalid cases).
#     - expected_status: Expected HTTP status code for the given invalid role ID.
#     - expected_detail: Expected error message in the response.
#
#     Test Scenarios:
#     1. Invalid ObjectId format.
#     2. Missing role ID (`None` value).
#     3. Non-positive integer values (0, -1).
#     4. Each scenario is tested with both:
#        - Super Admin user (with delete permissions).
#        - Regular User (without delete permissions).
#
#     Assertions:
#     - The API responds with the expected HTTP status code (400 for invalid inputs).
#     - The error message clearly indicates that the role ID is required and must be valid.
#     - Unauthorized users cannot delete roles.
#
#     This ensures robust error handling and proper authorization enforcement.
#     """
#
#     # testing with 'admin_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_role/{role_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing with 'user_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_role/{role_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Roles], indirect=True)
# async def test_delete_role_for_valid_id(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `delete_role` endpoint to verify successful role deletion.
#
#     This test checks the behavior of the `delete_role` API when provided with a valid role ID. It validates that:
#     - A super admin can successfully delete an existing role.
#     - Attempting to delete a non-existent role returns an appropriate error.
#     - Unauthorized users cannot delete roles.
#
#     Parameters:
#     - http_client_test: Async HTTP client used for sending API requests.
#     - fetch_latest_role_perm: Fixture providing the most recently created role object.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#     - role_id: The valid role ID to be deleted.
#
#     Test Scenarios:
#     1. Successful Deletion:
#        - Super admin deletes a valid role.
#     2. Deleting Non-existent Role:
#        - Attempting to delete the same role again returns a 400 error with a "Role doesn't exist" message.
#     3. Unauthorized Deletion:
#        - A regular user without appropriate permissions receives a 401 Unauthorized error.
#
#     Assertions:
#     - For a valid role ID, the response status is 200, and the message confirms successful deletion.
#     - Deleting a non-existent role returns a 400 status with an appropriate error message.
#     - Unauthorized users cannot delete roles and receive a 401 status with a relevant error message.
#
#     This test ensures proper authorization and accurate error handling for the role deletion functionality.
#     """
#
#     role_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_role/{role_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Role deleted successfully."
#
#     # testing with "super_admin_token" for non-existential data
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_role/{role_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == f"Role with id '{role_id}' doesn't exist."
#
#     # testing with "user_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_role/{role_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
