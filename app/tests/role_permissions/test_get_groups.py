"""
Unit tests for the `/role_permissions/groups` endpoint.

This module tests the group retrieval API with different scenarios, including:
- Authorization checks (missing, invalid, and valid tokens).
- Pagination handling with valid and invalid `page_num` and `page_size` values.
- Access control verification for Super Admin and regular users.

Test Scenarios:
---------------
1. Access without authentication:
   - No token
   - Invalid token
   - Missing headers

2. Pagination validation:
   - Valid `page_num` and `page_size`
   - Invalid `page_num` or `page_size`
   - Missing `page_num` or `page_size`

3. Group-based access control:
   - Super Admin: Successful retrieval on valid input.
   - Regular User: Access restricted.

Assertions:
-----------
- Status codes and response messages.
- Required fields (`data`, `total`, `count`, `pagination`, `message`).
- Unauthorized access for non-admin users.
"""
#TODO: need to add updated testcases for get_groups


import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_groups_without_token(http_client_test):
    """
    Handles unit test for the `groups` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/role_permissions/groups?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_groups_with_invalid_token(http_client_test, invalid_token):
    """
    Handles unit test for the `groups` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/role_permissions/groups?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_groups_without_headers(http_client_test):
    """
    Handles a unit test for the `groups` endpoint when called without headers.
    """
    response = await http_client_test.get(
        f"/role_permissions/groups?feature_key={feature_key}",
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
        ),  # test 'groups' with valid page_num and invalid page_size
        (
            1,
            None,
            400,
            "Page Size must be required and valid.",
        ),  # test 'groups' with valid page_num and no page_size
        (
            "one",
            10,
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with invalid page_num and valid page_size
        (
            "one",
            "ten",
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with invalid page_num and invalid page_size
        (
            "one",
            None,
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with invalid page_num and no page_size
        (
            None,
            10,
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with no page_num and valid page_size
        (
            None,
            "ten",
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with no page_num and invalid page_size
        (
            None,
            None,
            400,
            "Page Num must be required and valid.",
        ),  # test 'groups' with no page_num and no page_size
        # (
        #     1,
        #     10,
        #     200,
        #     "Groups Fetched Successfully",
        # ),  # test 'groups' with valid page_num and valid page_size
    ],
)
@pytest.mark.asyncio
async def test_get_groups(
    http_client_test,
    super_admin_token,
    user_token,
    page_num,
    page_size,
    expected_status,
    expected_detail,
):
    """
    Test the /role_permissions/groups endpoint.

    Validates group retrieval with pagination for Super Admin and regular users.
    Checks correct handling of valid and invalid `page_num` and `page_size` inputs.

    Parameters:
    - http_client_test (TestClient) : HTTP client for API requests.
    - super_admin_token (str) : Token for Super Admin access.
    - user_token (str) : Token for regular user access.
    - page_num (int/str/None) : Page number for pagination (valid/invalid cases).
    - page_size (int/str/None) : Page size for pagination (valid/invalid cases).
    - expected_status (int) : Expected HTTP status code.
    - expected_detail (str) : Expected message in the response.

    Assertions:
    - Validates status codes and response messages.
    - Ensures successful responses contain required fields.
    - Verifies access restrictions for regular users.
    """
    # testing with `admin_token`
    response = await http_client_test.get(
        f"/role_permissions/groups?page_num={page_num}&page_size={page_size}&feature_key={feature_key}",
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
        f"/role_permissions/groups?page_num={page_num}&page_size={page_size}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    if expected_status == 200:
        assert response.status_code == 401
        assert response.json()["detail"] == "You are not authorized to perform this action!"
    else:
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail
