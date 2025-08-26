"""
Unit Tests for the `delete_group` Endpoint

This module contains asynchronous pytest tests to validate the behavior of the `delete_group` endpoint.
The tests cover various scenarios including valid and invalid group deletion, authentication checks,
and permission enforcement.

Tested Endpoint:
    DELETE /role_permissions/delete_group/{group_id}

Fixtures:
    - http_client_test: Provides an asynchronous HTTP client for testing.
    - fetch_latest_role_perm: Fixture to fetch the most recently created group object.
    - super_admin_token: Provides a valid token for a Super Admin user.
    - user_token: Provides a valid token for a regular user.
    - invalid_token: Provides an invalid token for testing.

Test Scenarios:
    1. Unauthorized Access:
       - No token provided.
       - Missing authorization headers.
       - Invalid token usage.

    2. Invalid Group ID:
       - Non-existent group ID.
       - Improperly formatted ObjectId.
       - `None` as group ID.
       - Zero or negative group ID values.

    3. Valid Group Deletion:
       - Super Admin can delete a valid group successfully.
       - Deleting a non-existent group returns a 400 error.
       - Regular users without proper permissions cannot delete groups (401 Unauthorized).

Assertions:
    - HTTP status codes (200, 400, 401) are checked for correctness.
    - Appropriate error messages are validated for each scenario.
    - Access control is enforced between Super Admins and regular users.
"""

import pytest

from app.models.role_permission_schema import Groups
from app.tests.conftest import user_token
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_group_with_no_token(
    http_client_test, group_id=1
):
    """
    Handles a unit test for the `delete_group` endpoint when called with no token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_group/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_delete_group_without_headers(
    http_client_test, group_id=1
):
    """
    Handles a unit test for the `delete_group` endpoint when called without headers.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_group/{group_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_group_with_invalid_token(
    http_client_test,
    invalid_token,
    group_id=1,
):
    """
    Handles a unit test for the `delete_group` endpoint when called with an invalid token.
    """
    response = await http_client_test.delete(
        f"/role_permissions/delete_group/{group_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# Todo: Need to add updated testcases for delete_group
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "group_id, expected_status, expected_detail",
#     [
#         (
#             "65fad4822419830213cc4818",
#             400,
#             "Group Id must be required and valid.",
#         ),  # test delete_group with invalid group_id
#         (
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test delete_group with no group_id
#         (
#             0,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test delete_group with invalid group_id i.e. 0
#         (
#             -1,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test delete_group with invalid group_id i.e. negative
#     ],
# )
# async def test_delete_group_for_invalid_ids(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     group_id,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Unit test for the `delete_group` endpoint to validate handling of invalid group IDs.
#
#     This test ensures that the system correctly responds to invalid group identifiers when attempting to delete a group.
#     It checks the behavior for different invalid `group_id` values, including:
#     - An improperly formatted ObjectId.
#     - A `None` value (missing group ID).
#     - Zero or negative values.
#
#     Parameters:
#     - http_client_test: Async HTTP client used for sending API requests.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#     - group_id: The group ID to be tested (invalid cases).
#     - expected_status: Expected HTTP status code for the given invalid group ID.
#     - expected_detail: Expected error message in the response.
#
#     Test Scenarios:
#     1. Invalid ObjectId format.
#     2. Missing group ID (`None` value).
#     3. Non-positive integer values (0, -1).
#     4. Each scenario is tested with both:
#        - Super Admin user (with delete permissions).
#        - Regular User (without delete permissions).
#
#     Assertions:
#     - The API responds with the expected HTTP status code (400 for invalid inputs).
#     - The error message clearly indicates that the group ID is required and must be valid.
#     - Unauthorized users cannot delete groups.
#
#     This ensures robust error handling and proper authorization enforcement.
#     """
#
#     # testing with 'admin_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing with 'user_token'
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Groups], indirect=True)
# async def test_delete_group_for_valid_id(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `delete_group` endpoint to verify successful group deletion.
#
#     This test checks the behavior of the `delete_group` API when provided with a valid group ID. It validates that:
#     - A super admin can successfully delete an existing group.
#     - Attempting to delete a non-existent group returns an appropriate error.
#     - Unauthorized users cannot delete groups.
#
#     Parameters:
#     - http_client_test: Async HTTP client used for sending API requests.
#     - fetch_latest_role_perm: Fixture providing the most recently created group object.
#     - super_admin_token: Authorization token for a super admin user.
#     - user_token: Authorization token for a regular user.
#     - group_id: The valid group ID to be deleted.
#
#     Test Scenarios:
#     1. Successful Deletion:
#        - Super admin deletes a valid group.
#     2. Deleting Non-existent Group:
#        - Attempting to delete the same group again returns a 400 error with a "Group doesn't exist" message.
#     3. Unauthorized Deletion:
#        - A regular user without appropriate permissions receives a 401 Unauthorized error.
#
#     Assertions:
#     - For a valid group ID, the response status is 200, and the message confirms successful deletion.
#     - Deleting a non-existent group returns a 400 status with an appropriate error message.
#     - Unauthorized users cannot delete groups and receive a 401 status with a relevant error message.
#
#     This test ensures proper authorization and accurate error handling for the group deletion functionality.
#     """
#
#     group_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Group deleted successfully."
#
#     # testing with "super_admin_token" for non-existential data
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == f"Group with id '{group_id}' doesn't exist."
#
#     # testing with "user_token"
#     response = await http_client_test.delete(
#         f"/role_permissions/delete_group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
