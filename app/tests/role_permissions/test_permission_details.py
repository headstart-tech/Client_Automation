"""
Unit tests for the `/role_permissions/permissions/{permission_id}` endpoint.

This test suite verifies the behavior of the endpoint under various scenarios, including:
1. Authorization checks (valid, invalid, and missing tokens).
2. Input validation for `permission_id` (missing, invalid types, zero, and negative values).
3. Successful permission retrieval for authorized users (Super Admin).
4. Access denial for unauthorized users (Regular User).

Test Cases:
1. **test_get_role_without_token**: Ensures the endpoint returns a `401 Unauthorized` error when no token is provided.
2. **test_get_role_with_invalid_token**: Ensures the endpoint returns a `401 Unauthorized` error when an invalid token is provided.
3. **test_get_role_without_headers**: Ensures the endpoint returns a `401 Unauthorized` error when authorization headers are missing.
4. **test_get_permission**: Validates input errors for invalid `permission_id` values across both Super Admin and Regular User contexts.
5. **test_get_role_with_valid_data**: Verifies successful permission retrieval for Super Admin and ensures Regular User access is denied.

Fixtures:
- `http_client_test`: HTTP client to simulate API requests.
- `super_admin_token`: Authorization token with Super Admin privileges.
- `user_token`: Authorization token with Regular User privileges.
- `invalid_token`: Invalid authorization token.
- `fetch_latest_role_perm`: Fixture to fetch the latest permission record.

Assertions:
- Proper HTTP status codes for each scenario (200, 400, 401).
- Correct error messages for invalid inputs and unauthorized access.
- Accurate permission data for valid requests with Super Admin access.
"""

import pytest

from app.models.role_permission_schema import Permission
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_role_without_token(http_client_test):
    """
    Handles unit test for the `/permissions/{permission_id}` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/role_permissions/permissions/1?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_role_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `/permissions/{permission_id}` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/role_permissions/permissions/1?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_role_without_headers(http_client_test):
    """
    Handles a unit test for the `/permissions/{permission_id}` endpoint when called without headers.
    """
    response = await http_client_test.get(
        f"/role_permissions/permissions/1?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permission_id, expected_status, expected_detail",
    [
        (
            None,
            400,
            "Permission Id must be required and valid.",
        ),  # test `/permissions/{permission_id}` without permission id.
        (
            "65f41ec543d505076037221",
            400,
            "Permission Id must be required and valid.",
            # test `/permissions/{permission_id}` with invalid permission id, i.e. str
        ),
        (
            0,
            400,
            "Permission Id must be required and valid.",
            # test `/permissions/{permission_id}` with invalid permission id, i.e. 0.
        ),
        (
            -2,
            400,
            "Permission Id must be required and valid.",
            # test `/permissions/{permission_id}` with invalid permission id, i.e. negative
        ),
    ],
)
async def test_get_permission(http_client_test, super_admin_token, user_token, permission_id, expected_status, expected_detail):
    """
    Unit test for the `/role_permissions/permissions/{permission_id}` endpoint.

    Scenarios:
    - **Super Admin & Regular User**: Validates error handling for invalid `permission_id` values.
      - Missing permission ID.
      - Invalid string format.
      - Zero or negative ID.

    Parameters:
    - http_client_test: HTTP client for API requests.
    - super_admin_token: Token for Super Admin access.
    - user_token: Token for regular user access.
    - permission_id: Test permission ID (valid/invalid cases).
    - expected_status: Expected HTTP status code.
    - expected_detail: Expected error message.

    Assertions:
    - Validates status codes and error messages for invalid inputs.
    """

    # testing with "super_admin_token"
    response = await http_client_test.get(
        f"/role_permissions/permissions/{permission_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

    # testing with "user_token"
    response = await http_client_test.get(
        f"/role_permissions/permissions/{permission_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

# Todo: Need to add updated testcases for permission_details

# @pytest.mark.asyncio
# @pytest.mark.parametrize("fetch_latest_role_perm", [Permission], indirect=True)
# async def test_get_role_with_valid_data(http_client_test, fetch_latest_role_perm, super_admin_token, user_token):
#     """
#     Unit test for the `/role_permissions/permissions/{permission_id}` endpoint.
#
#     Scenarios:
#     - **Super Admin**: Successfully fetches permission details with required fields.
#     - **Regular User**: Access denied with a `401 Unauthorized` response.
#
#     Parameters:
#     - http_client_test: HTTP client for API requests.
#     - fetch_latest_role_perm: Fixture to fetch the latest permission.
#     - super_admin_token: Token for Super Admin access.
#     - user_token: Token for regular user access.
#
#     Assertions:
#     - Validates status codes and response fields.
#     """
#     permission_id = fetch_latest_role_perm.id
#
#     # testing with "super_admin_token"
#     response = await http_client_test.get(
#         f"/role_permissions/permissions/{permission_id}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Permission Fetched Successfully"
#     response_data = response.json()
#     assert all(
#         field_name in response_data.get("data", [])
#         for field_name in [
#             "id",
#             "name",
#             "description",
#         ]
#     )
#
#     # testing with "user_token"
#     response = await http_client_test.get(
#         f"/role_permissions/permissions/{permission_id}",
#         headers={"Authorization": f"Bearer {user_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "You are not authorized to perform this action!"
