"""
Unit tests for the `/assign_permission/group/` endpoint in the Role Permissions module.

These tests cover different scenarios to ensure that permission assignment behaves as expected.

Test Scenarios:

1. **Authentication Tests:**
    - Without any authorization token (expects 401 Unauthorized).
    - With an invalid authorization token (expects 401 Unauthorized).
    - Without authorization headers (expects 401 Unauthorized).

2. **Input Validation Tests:**
    - Invalid or None group ID with various JSON payloads (expects 400 Bad Request).
    - Valid group ID with invalid JSON payload (expects 400 Bad Request).

3. **Permission Assignment Tests:**
    - Successful permission assignment with a valid group ID and unassigned permission (expects 200 OK).
    - Reassigning an already assigned permission (expects no new additions with 200 OK).
    - Sending `None` as the JSON payload (expects no new additions with 200 OK).
    - Unauthorized access by a regular user attempting to assign permissions (expects 401 Unauthorized).

Fixtures:
    - http_client_test: Provides an HTTP client for making asynchronous test requests.
    - super_admin_token: Authorization token with Super Admin privileges.
    - user_token: Authorization token with User privileges.
    - invalid_token: Invalid authorization token for negative testing.
    - fetch_latest_role_perm: Fixture for retrieving the latest available group.
"""

import pytest

from app.models.role_permission_schema import Groups
from app.tests.conftest import fetch_unassigned_permission
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_assign_permission_without_token(http_client_test):
    """
    Handles unit test for the `/assign_permission/group/` endpoint when called with no authorization token.
    """
    response = await http_client_test.post(
        f"/role_permissions/assign_permission/group/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_assign_permission_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `/assign_permission/group/` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/assign_permission/group/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_assign_permission_without_headers(http_client_test):
    """
    Handles unit test for the `/assign_permission/group/` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/assign_permission/group/1?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Todo: Need to add updated testcases for assign_permissions to group.

# @pytest.mark.asyncio
# async def test_assign_permission_without_request_body(http_client_test, super_admin_token):
#     """
#     Handles unit test for the `/assign_permission/group/` endpoint when called without request body.
#     """
#
#     response = await http_client_test.post(
#         "/role_permissions/assign_permission/group/1",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=None,
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "No permissions were added."

#
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "group_id, user_request, expected_status, expected_detail",
#     [
#         (
#             "65f989b3fe903811ed285a9",
#             [],
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with invalid id and valid json
#         (
#             "ID",
#             "Permission list",
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with invalid id and invalid json
#         (
#             0,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with invalid id and None json
#         (
#             None,
#             [],
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with None id and valid json
#         (
#             None,
#             False,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with None id and invalid json
#         (
#             None,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test "/assign_permission/group/" with None id and None json
#         (
#             1,
#             "Permission list",
#             400,
#             "Body must be required and valid.",
#         ),  # test "/assign_permission/group/" with valid id and invalid json
#     ],
# )
# async def test_assign_permission_for_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     group_id,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Test assigning permissions with invalid data for both super admin and user tokens.
#
#     Scenarios tested:
#     1. Invalid group ID with valid, invalid, or None JSON payload.
#     2. None group ID with valid, invalid, or None JSON payload.
#     3. Valid group ID with invalid JSON payload.
#
#     Params:
#         http_client_test: HTTP client for async test requests.
#         super_admin_token: Token for a super admin.
#         user_token: Token for a regular user.
#         group_id: Group ID parameter (invalid or None).
#         user_request: JSON payload with permissions (invalid, None, or empty list).
#         expected_status: Expected HTTP status code (400 for all cases).
#         expected_detail: Expected error message in the response.
#     """
#
#     # testing "/assign_permission/group/" with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing "/assign_permission/group/" with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Groups], indirect=True)
# async def test_assign_permission_with_valid_data(
#     http_client_test, fetch_latest_role_perm, user_token, super_admin_token
# ):
#     """Test assigning permissions to a group with various scenarios.
#
#     Scenarios tested:
#     1. Assigning a valid permission (expects success).
#     2. Reassigning an already assigned permission (expects no new additions).
#     3. Sending None as JSON payload (expects no new additions).
#     4. Unauthorized access with a regular user (expects an authorization error).
#
#     Params:
#         http_client_test: HTTP client for async test requests.
#         fetch_latest_role_perm: Fixture for the latest group instance.
#         user_token: Token for a regular user.
#         super_admin_token: Token for a super admin.
#     """
#     group_id = fetch_latest_role_perm.id
#     perm_id = await fetch_unassigned_permission("group", group_id)
#
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=[perm_id],
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Permissions assigned successfully."
#
#     # testing with "super_admin_token" with already assigned id
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=[perm_id],
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "No permissions were added."
#
#     # testing with "super_admin_token" with None JSON
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=None,
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "No permissions were added."
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/assign_permission/group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=[perm_id],
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
