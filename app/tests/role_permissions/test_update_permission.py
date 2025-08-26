"""
Unit tests for the `/role_permissions/update_permission/{permission_id}` endpoint.

This module contains a comprehensive set of tests to validate the behavior of the permission update functionality,
including scenarios for valid updates, invalid inputs, and authorization checks.

Test Scenarios:

1. **Unauthorized Access:**
    - Without an authorization token.
    - Without authorization headers.
    - With an invalid authorization token.

2. **Invalid Input Data:**
    - Missing request body.
    - Invalid or None `permission_id`.
    - Invalid request payload (e.g., incorrect data types).

3. **Valid Data and Authorization:**
    - Successful permission update by a Super Admin.
    - Unauthorized update attempt by a regular user.
    - Attempting to update a permission with a duplicate name.

Parameters:

- `http_client_test`: Simulated HTTP client for testing.
- `super_admin_token`: Authorization token for Super Admin.
- `user_token`: Authorization token for a regular user.
- `invalid_token`: Invalid authorization token.
- `permission_id`: ID of the permission to be updated.
- `user_request`: JSON payload containing updated permission data.

Assertions:

- Validates correct HTTP status codes and error messages.
- Ensures only Super Admins can update permissions.
- Confirms proper handling of invalid inputs and duplicate names.

Fixtures:

- `fetch_latest_role_perm`: Fetches the latest permission object from the database.

Test Methods:

- `test_update_permission_without_token`: Checks unauthorized access without a token.
- `test_update_permission_without_headers`: Checks unauthorized access without headers.
- `test_update_permission_with_invalid_token`: Validates access with an invalid token.
- `test_update_permission_without_request_body`: Ensures 400 error for missing request body.
- `test_update_permission_for_invalid_data`: Covers various invalid `permission_id` and payload cases.
- `test_update_permission_with_valid_data`: Validates successful updates and duplicate name handling.

"""

import json
import time

import pytest

from app.models.role_permission_schema import Permission
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_permission_without_token(
    http_client_test, permission_id=1
):
    """
    This functionality contains a unit test for the `update_permission` endpoint when called with no authorization token.
    """
    response = await http_client_test.put(
        f"/role_permissions/update_permission/{permission_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_update_permission_without_headers(
    http_client_test, permission_id=1
):
    """
    This functionality contains a unit test for the `update_permission` endpoint when called without headers.
    """
    response = await http_client_test.put(
        f"/role_permissions/update_permission/{permission_id}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_permission_with_invalid_token(
    http_client_test, invalid_token, permission_id=1
):
    """
    This functionality contains unit test for the `update_permission` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.put(
        f"/role_permissions/update_permission/{permission_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_update_permission_without_request_body(
    http_client_test, super_admin_token, permission_id="65f989b3fe903811ed285a97"
):
    """
    This functionality contains unit test for the `update_permission` endpoint when called without request body.
    """

    response = await http_client_test.put(
        f"/role_permissions/update_permission/{permission_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=None,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Permission Id must be required and valid."


# Todo: Need to add updated testcases for update_permission

# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "permission_id, user_request, expected_status, expected_detail",
#     [
#         (
#             "65f989b3fe903811ed285a9",
#             {
#                 "name": f"permission_{time.time()}",
#                 "description": "description",
#             },
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with invalid id and valid json
#         (
#             "65f989b3fe903811ed285a9",
#             {
#                 "name": f"permission_{time.time()}",
#                 "description": 100,
#             },
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with invalid id and invalid json
#         (
#             0,
#             None,
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with invalid id and None json
#         (
#             None,
#             {
#                 "name": f"permission_{time.time()}",
#                 "description": "description",
#             },
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with None id and valid json
#         (
#             None,
#             {
#                 "name": f"permission_{time.time()}",
#                 "description": 100,
#             },
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with None id and invalid json
#         (
#             None,
#             None,
#             400,
#             "Permission Id must be required and valid.",
#         ),  # test update_permission with None id and None json
#     ],
# )
# async def test_update_permission_for_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     permission_id,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Unit test for `/role_permissions/update_permission/{permission_id}` endpoint with invalid data.
#
#     Tests:
#     1. Validation errors for invalid `permission_id` and request payload.
#     2. Ensures consistent error handling for both Super Admin and regular users.
#
#     Parameters:
#     - `http_client_test`: Simulated HTTP client.
#     - `super_admin_token`: Super Admin token.
#     - `user_token`: Regular user token.
#     - `permission_id`: Invalid or None permission ID.
#     - `user_request`: Request payload (valid, invalid, or None).
#     - `expected_status`: Expected HTTP status code.
#     - `expected_detail`: Expected error message.
#
#     Assertions:
#     - Ensures 400 status and appropriate error messages for invalid data.
#     - Consistent behavior for both Super Admin and regular users.
#     """
#     user_requested_data = json.dumps(user_request) if user_request else "{}"
#
#     # testing "update_permission" with "super_admin_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_permission/{permission_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#     # testing "update_permission" with "user_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_permission/{permission_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Permission], indirect=True)
# async def test_update_permission_with_valid_data(
#     http_client_test, fetch_latest_role_perm, user_token, super_admin_token
# ):
#     """
#     Unit test for `/role_permissions/update_permission/{permission_id}` endpoint.
#
#     Tests:
#     1. Successful permission update by a Super Admin.
#     2. Unauthorized update attempt by a regular user.
#     3. Duplicate permission name error.
#
#     Parameters:
#     - `http_client_test`: Simulated HTTP client.
#     - `fetch_latest_role_perm`: Fixture fetching the latest permission.
#     - `user_token`: Regular user token.
#     - `super_admin_token`: Super Admin token.
#
#     Assertions:
#     - 200 status for valid updates by Super Admin.
#     - 401 status for unauthorized users.
#     - 400 status for duplicate permission names.
#     """
#
#     # testing with "super_admin_token"
#     perm_name = f"permission_{time.time()}"
#     permission_id = fetch_latest_role_perm.id
#     json_obj = {"name": perm_name, "description": None}
#
#     # testing with "super_admin_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_permission/{permission_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Permission updated successfully."
#
#     # testing with "user_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_permission/{permission_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
#     json_obj.update({"name": "super_admin"})
#     # testing update_permission with duplicate name with "super_admin_token"
#     response = await http_client_test.put(
#         f"/role_permissions/update_permission/{permission_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Permission already exists with name 'super_admin'."
