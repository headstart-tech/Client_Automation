"""
Unit Tests for the `create_permission` Endpoint

This module contains test cases to validate the behavior of the `create_permission` endpoint
for creating role-based permissions in the system. The tests cover various scenarios, including:

1. **Unauthorized Access**:
   - Without an authorization token.
   - With an invalid authorization token.
   - Without authorization headers.

2. **Invalid Input Data**:
   - Missing request body.
   - Invalid JSON payloads (e.g., incorrect data types or null values).

3. **Valid Input Data**:
   - Successful creation of a permission by a super admin.
   - Unauthorized access when a regular user tries to create a permission.

4. **Duplicate Data**:
   - Attempting to create a permission with a duplicate name.

Test Parameters:
- `http_client_test`: Asynchronous HTTP client for sending test requests.
- `super_admin_token`: Authorization token for a super admin.
- `user_token`: Authorization token for a regular user.
- `invalid_token`: An invalid authorization token for testing unauthorized access.
- `user_request`: JSON payload to create a new permission.
- `fetch_latest_role_perm`: Fixture to retrieve the most recent permission from the database.

Assertions:
- Verify appropriate status codes (401 for unauthorized, 400 for bad requests, 201 for success).
- Ensure proper error messages are returned for invalid and duplicate requests.
- Check that valid responses contain the required fields ("name" and "description").
"""

import time

import pytest

from app.models.role_permission_schema import Permission
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_permission_without_token(http_client_test):
    """
    Handles unit test for the `create_permission` endpoint when called with no authorization token.
    """
    response = await http_client_test.post(
        f"/role_permissions/create_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_create_permission_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `create_permission` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_create_permission_without_headers(http_client_test):
    """
    Handles unit test for the `create_permission` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_permission/?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_permission_without_request_body(http_client_test, super_admin_token):
    """
    Handles unit test for the `create_permission` endpoint when called without request body.
    """

    response = await http_client_test.post(
        f"/role_permissions/create_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=None,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."

# Todo: Need to add updated testcases for create_permission

#
# @pytest.mark.parametrize(
#     "user_request, expected_status, expected_detail",
#     [
#         (
#             {
#                 "name": 121,
#                 "description": None,
#             },
#             400,
#             "Name must be required and valid.",
#         ),  # test create_permission with invalid json
#         (
#             {
#                 "name": None,
#                 "description": None,
#             },
#             400,
#             "Name must be required and valid.",
#         ),  # test create_permission with invalid json
#         (
#             None,
#             400,
#             "Body must be required and valid.",
#         ),  # test create_permission with None json
#     ],
# )
# async def test_create_permission_with_invalid_data(
#     http_client_test,
#     super_admin_token,
#     user_token,
#     user_request,
#     expected_status,
#     expected_detail,
# ):
#     """
#     Test the `create_permission` endpoint with invalid data.
#
#     Params:
#         - http_client_test: HTTP client for making test requests.
#         - super_admin_token: Access token for a super admin.
#         - user_token: Access token for a regular user.
#         - user_request: JSON payload for creating a permission.
#         - expected_status: Expected HTTP status code.
#         - expected_detail: Expected error message.
#
#     Asserts:
#         - Both super admin and user requests return the expected status and detail.
#         - For valid creation (201 status), check that "name" and "description" exist in the response.
#     """
#
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_permission/",
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
#         f"/role_permissions/create_permission/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == expected_status
#     assert response.json()["detail"] == expected_detail
#
#
# @pytest.mark.parametrize(
#     "user_request",
#     [
#         {
#             "name": f"permission_{time.time()}",
#             "description": None,
#         },  # test create_permission with valid json
#     ],
# )
# async def test_create_permission_with_valid_data(
#     http_client_test,
#     user_token,
#     super_admin_token,
#     user_request,
# ):
#     """
#     Handles unit test for the `create_permission` endpoint when called with user authorization token.
#
#     Params:
#         - http_client_test: HTTP client for making test requests.
#         - user_token: Access token for a regular user.
#         - super_admin_token: Access token for a super admin.
#         - user_request: JSON payload for creating a permission.
#
#     Asserts:
#         - Super admin: 201 status with "Permission created successfully." message.
#         - User: 401 status with "You are not authorized to perform this action!" message.
#         - Response contains "name" and "description" fields.
#     """
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_permission/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=user_request,
#     )
#     assert response.status_code == 201
#     assert response.json()["message"] == "Permission created successfully."
#     response_data = response.json()["data"]
#     for field_name in [
#         "name",
#         "description",
#     ]:
#         assert field_name in response_data
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         f"/role_permissions/create_permission/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=user_request,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
#
#
# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Permission], indirect=True)
# async def test_create_permission_with_duplicate_data(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Test creating a permission with duplicate data.
#
#     This test verifies that:
#     1. A "super_admin" user cannot create a permission with a duplicate name.
#     2. A regular user is not authorized to create permissions.
#
#     Params:
#         http_client_test (AsyncClient): HTTP client for making test requests.
#         fetch_latest_role_perm (Permission): The most recent permission from the database.
#         super_admin_token (str): Access token for a super admin user.
#         user_token (str): Access token for a regular user.
#
#     Asserts:
#         - Super admin receives a 400 status with a "Permission already exists" error.
#         - Regular user receives a 401 status with an "unauthorized" error.
#     """
#     duplicate_name = fetch_latest_role_perm.name
#     json_obj = {
#         "name": duplicate_name,
#         "description": "Testing duplicate insertion."
#     }
#
#     # testing with "super_admin_token"
#     response = await http_client_test.post(
#         "/role_permissions/create_permission/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == f"Permission already exists with name '{duplicate_name}'."
#
#     # testing with "user_token"
#     response = await http_client_test.post(
#         "/role_permissions/create_permission/",
#         headers={"Authorization": f"Bearer {user_token}"},
#         json=json_obj,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
