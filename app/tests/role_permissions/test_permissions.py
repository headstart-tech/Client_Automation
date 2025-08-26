"""
Unit tests for the `/role_permissions/permissions` endpoint.

These tests cover various scenarios, including:
1. Authorization checks with valid, invalid, and missing tokens.
2. Validation of pagination parameters (`page_num` and `page_size`).
3. Ensuring proper access control for Super Admin and regular users.
4. Response structure and error handling.

Test Cases:
- `test_get_permissions_without_token`: Ensures requests without an authorization token return a 401 status.
- `test_get_role_with_invalid_token`: Ensures requests with an invalid token return a 401 status.
- `test_get_permissions_without_headers`: Ensures requests without any headers return a 401 status.
- `test_get_permissions`: Parameterized test to validate:
    - Different combinations of valid and invalid `page_num` and `page_size`.
    - Super Admin access with correct response structure for valid requests.
    - Unauthorized response for regular users accessing the endpoint.

Parameters:
- `http_client_test`: Simulated HTTP client for making requests.
- `super_admin_token`: Authorization token for Super Admin.
- `user_token`: Authorization token for a regular user.
- `invalid_token`: Invalid authorization token.
- `page_num`: Page number for pagination (should be a valid integer).
- `page_size`: Page size for pagination (should be a valid integer).
- `expected_status`: Expected HTTP status code.
- `expected_detail`: Expected message or error detail.

Assertions:
- Ensures proper status codes and error messages for invalid requests.
- Confirms correct data structure in valid responses.
- Validates access control by restricting regular users.
"""
#TODO: need to add updated testcases for get_permissions

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_permissions_without_token(http_client_test):
    """
    Handles unit test for the `permissions` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/role_permissions/permissions?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_role_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `permissions` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/role_permissions/permissions?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_permissions_without_headers(http_client_test):
    """
    Handles a unit test for the `permissions` endpoint when called without headers.
    """
    response = await http_client_test.get(
        f"/role_permissions/permissions?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "page_num, page_size, expected_status, expected_detail",
    [
        (
            1,
            "ten",
            400,
            "Page Size must be required and valid.",
        ),  # test 'permissions' with valid page_num and invalid page_size
        (
            1,
            None,
            400,
            "Page Size must be required and valid.",
        ),  # test 'permissions' with valid page_num and no page_size
        (
            "one",
            10,
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with invalid page_num and valid page_size
        (
            "one",
            "ten",
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with invalid page_num and invalid page_size
        (
            "one",
            None,
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with invalid page_num and no page_size
        (
            None,
            10,
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with no page_num and valid page_size
        (
            None,
            "ten",
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with no page_num and invalid page_size
        (
            None,
            None,
            400,
            "Page Num must be required and valid.",
        ),  # test 'permissions' with no page_num and no page_size
        # (
        #     1,
        #     10,
        #     200,
        #     "Permissions Fetched Successfully",
        # ),  # test 'permissions' with valid page_num and valid page_size
    ],
)
@pytest.mark.asyncio
async def test_get_permissions(
    http_client_test,
    super_admin_token,
    user_token,
    page_num,
    page_size,
    expected_status,
    expected_detail,
):
    """
    Unit tests for the `/role_permissions/permissions` endpoint with pagination.

    Tests:
    1. Validates `page_num` and `page_size` inputs.
    2. Ensures Super Admin can fetch permissions successfully.
    3. Confirms unauthorized access for regular users.

    Parameters:
    - `http_client_test`: Simulated HTTP client.
    - `super_admin_token`: Token for Super Admin.
    - `user_token`: Token for Regular User.
    - `page_num`, `page_size`: Pagination parameters.
    - `expected_status`, `expected_detail`: Expected response details.

    Assertions:
    - Status codes and error messages for invalid inputs.
    - Correct response structure for valid requests.
    - Unauthorized access for regular users.
    """

    # testing with `admin_token`
    response = await http_client_test.get(
        f"/role_permissions/permissions?page_num={page_num}&page_size={page_size}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        assert response.json()["message"] == expected_detail
        response_data = response.json()
        for field_name in [
            "data",
            "total",
            "count",
            "pagination",
            "message",
        ]:
            assert field_name in response_data
    else:
        assert response.json()["detail"] == expected_detail

    # testing with `user_token`
    response = await http_client_test.get(
        f"/role_permissions/permissions?page_num={page_num}&page_size={page_size}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    if expected_status == 200:
        assert response.status_code == 401
        assert response.json()["detail"] == "You are not authorized to perform this action!"
    else:
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail
