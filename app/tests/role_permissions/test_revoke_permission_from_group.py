"""
Unit tests for the `revoke_permissions/group` endpoint.

This module validates the `revoke_permissions/group` API behavior under different scenarios:

1. **Unauthorized Access**:
   - No token: Ensures the API returns a 401 status with "Could not validate credentials".
   - Invalid token: Ensures the API returns a 401 status with "Could not validate credentials".
   - Missing headers: Ensures the API returns a 401 status with "Not authenticated".

2. **Invalid Data Handling**:
   - Invalid group IDs (e.g., None, malformed, or non-existent).
   - Invalid request payloads (e.g., None, non-list, or empty list).
   - Ensures the API returns a 400 status with appropriate error messages.

3. **Valid Data Handling**:
   - Super Admin:
     - Can revoke valid permissions for a group.
     - Receives a confirmation message if permissions are revoked.
     - Receives a "No permissions were removed" message if no valid permissions are provided.
   - Regular User:
     - Cannot revoke permissions (returns 401 Unauthorized).

Test Parameters:
http_client_test : AsyncClient
    Asynchronous HTTP client for API requests.
super_admin_token : str
    Authorization token with Super Admin privileges.
user_token : str
    Authorization token with regular User privileges.
invalid_token : str
    An invalid authorization token for testing unauthorized access.
fetch_latest_role_perm : Group
    Fixture providing the latest group with permissions.
group_id : Any
    The group identifier (valid, invalid, or None).
user_request : Any
    JSON request payload (valid, invalid, or None).
expected_status : int
    The expected HTTP status code from the API.
expected_detail : str
    The expected error message from the API response.

Test Coverage:
- Authorization checks (valid, invalid, and missing tokens).
- Input validation (group ID and payload).
- Permission revocation for valid and invalid cases.
- Differentiates behavior for Super Admins and regular Users.

"""
import random
import pytest

from app.models.role_permission_schema import Groups
from app.tests.conftest import fetch_assigned_permission_ids
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_revoke_permission_without_token(http_client_test):
    """
    Handles unit test for the `revoke_permission` endpoint when called with no authorization token.
    """
    response = await http_client_test.post(
        f"/role_permissions/revoke_permissions/group/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_revoke_permission_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `revoke_permission` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/revoke_permissions/group/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_revoke_permission_without_headers(http_client_test):
    """
    Handles unit test for the `revoke_permission` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/revoke_permissions/group/1?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Todo: Need to add updated testcases for revoke_permissions from group

# @pytest.mark.asyncio
# async def test_revoke_permission_without_request_body(http_client_test, super_admin_token):
#     """
#     Handles unit test for the `revoke_permission` endpoint when called without request body.
#     """
#
#     response = await http_client_test.post(
#         "/role_permissions/revoke_permissions/group/1",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=None,
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "No permissions were removed."

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
#         ),  # test assign_permission with invalid id and valid json
#         (
#             "ID",
#             "Permission list",
#             400,
#             "Group Id must be required and valid.",
#         ),  # test assign_permission with invalid id and invalid json
#         (
#             0,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test assign_permission with invalid id and None json
#         (
#             None,
#             [],
#             400,
#             "Group Id must be required and valid.",
#         ),  # test assign_permission with None id and valid json
#         (
#             None,
#             False,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test assign_permission with None id and invalid json
#         (
#             None,
#             None,
#             400,
#             "Group Id must be required and valid.",
#         ),  # test assign_permission with None id and None json
#         (
#             1,
#             "Permission list",
#             400,
#             "Body must be required and valid.",
#         ),  # test assign_permission with valid id and invalid json
#     ],
# )
# async def test_revoke_permission_for_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     group_id,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Test the 'revoke_permissions/group' endpoint with invalid data.
#
#     Ensures the API returns a 400 status code and appropriate error messages for:
#     - Invalid group IDs (e.g., None, malformed, or non-existent).
#     - Invalid request payloads (e.g., None, non-list, or empty list).
#
#     Parameters:
#     - http_client_test : AsyncClient - Async HTTP client for API requests.
#     - super_admin_token : str - Token for Super Admin access.
#     - user_token : str - Token for regular User access.
#     - group_id : Any - Group ID (invalid or None).
#     - user_request : Any - JSON payload (invalid or None).
#     - expected_status : int - Expected HTTP status code.
#     - expected_detail : str - Expected error message.
#     """
#
#
#     # testing "revoke_permission" with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/revoke_permissions/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing "revoke_permission" with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/revoke_permissions/group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Groups], indirect=True)
# async def test_revoke_permission_with_valid_data(
#     http_client_test, fetch_latest_role_perm, user_token, super_admin_token
# ):
#     """
#     Test the 'revoke_permissions/group' endpoint.
#
#     Validates permission revocation for a group under different scenarios:
#
#     1. Super Admin:
#        - Can revoke valid permissions.
#        - Receives a message if no permissions are removed.
#     2. Regular User:
#        - Cannot revoke permissions (returns 401 Unauthorized).
#
#     Parameters:
#     -----------
#     http_client_test : AsyncClient
#         Asynchronous HTTP client for API requests.
#     fetch_latest_role_perm : Group
#         Fixture providing the latest group with permissions.
#     user_token : str
#         Authorization token for a regular user.
#     super_admin_token : str
#         Authorization token for a super-admin.
#
#     """
#
#     group_id = fetch_latest_role_perm.id
#     perm_data = await fetch_assigned_permission_ids("group", group_id)
#
#     # testing with "super_admin_token" with empty list
#     response = await http_client_test.post(
#         f"/role_permissions/revoke_permissions/group/{group_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=[],
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "No permissions were removed."
#
#     # testing with "user_token" with empty list
#     response = await http_client_test.post(
#         f"/role_permissions/revoke_permissions/group/{group_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=[],
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
#     if perm_data:
#         prem_id = [random.choice(perm_data)]
#
#         # testing with "super_admin_token" with existing permission id
#         response = await http_client_test.post(
#             f"/role_permissions/revoke_permissions/group/{group_id}",
#             headers={"Authorization": f"Bearer {super_admin_token}"},
#             json=prem_id,
#         )
#         assert response.status_code == 200
#         assert response.json()["message"] == "Permissions revokeed successfully."
#
#         # testing with "super_admin_token" with non-existing permission id
#         response = await http_client_test.post(
#             f"/role_permissions/revoke_permissions/group/{group_id}",
#             headers={"Authorization": f"Bearer {super_admin_token}"},
#             json=prem_id,
#         )
#         assert response.status_code == 200
#         assert response.json()["message"] == "No permissions were removed."
#
#         # testing with "user_token"
#         response = await http_client_test.post(
#             f"/role_permissions/revoke_permissions/group/{group_id}",
#             headers={"Authorization": f"Bearer {user_token}"},
#             json=prem_id,
#         )
#         assert response.status_code == 401
#         assert response.json()["detail"] == "You are not authorized to perform this action!"
