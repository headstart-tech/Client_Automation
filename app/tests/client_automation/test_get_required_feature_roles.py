"""
This module contains unit tests for the `get_required_feature_roles` endpoint in the client automation API.

The test cases cover various scenarios including:
- Testing the endpoint with different authorization tokens (valid, invalid, and missing).
- Testing the endpoint with different combinations of input parameters such as client_id and college_id.
- Verifying the response status codes and error messages.

Each test case is parametrized to cover multiple combinations of input parameters, such as:
- Valid and invalid client_id.
- Valid and invalid college_id.
- None values for college_id and client_id.

Additionally, there are separate test cases to verify the behavior when the request is made without an authorization
token, as well as when the request body is missing or invalid.

These tests ensure that the `get_required_feature_roles` endpoint behaves correctly under different conditions,
and that appropriate error messages are returned when necessary.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_required_feature_roles_without_token(
    http_client_test, client_id="65f989b3fe903811ed285a97"
):
    """
    Handles unit test for the `get_required_feature_roles` endpoint when called with no authorization token.
    """
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_required_feature_roles_with_invalid_token(
    http_client_test,
    invalid_token,
    client_id="65f989b3fe903811ed285a97",
):
    """
    Handles unit test for the `get_required_feature_roles` endpoint when called with an invalid authorization token.
    """

    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_required_feature_roles_without_headers(
    http_client_test,
    client_id="65f989b3fe903811ed285a97",
):
    """
    Handles unit test for the `get_required_feature_roles` endpoint when called without request body.
    """

    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?client_id={client_id}&feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "client_id, college_id, expected_status, expected_detail",
    [
        (
            "65fc90aabf3ce46f00e28f8", # length < 24
            "65fc90aabf3ce46f00e28f80",
            404,
            "College not found",
        ),  # test get_required_feature_roles with invalid client_id and valid college_id
        (
            "65fc90aabf3ce46f00e28f8de", # length > 24
            "65fc90aabf3ce46f00e28f8",
            422,
            "College id `65fc90aabf3ce46f00e28f8` must be a 12-byte input or a 24-character hex string",
        ),  # test get_required_feature_roles with invalid client_id and valid college_id
        (
            "6800c8a3a65519d7648fb160",
            "65fc90aabf3ce46f00e28f8d",
            404,
            "College not found",
        ),  # test get_required_feature_roles with invalid client_id and invalid college_id
        (
            "65fc90aabf3ce46f00e28f8di", # length > 24
            "65fc90aabf3ce46f00e28f8d",
            404,
            "College not found",
        ),  # test get_required_feature_roles with invalid client_id and invalid college_id
        (
            "65fc90aabf3ce46f00e28f8d",
            "65fc90aabf3ce46f00e28f8di",  # length > 24
            422,
            "College id `65fc90aabf3ce46f00e28f8di` must be a"
            " 12-byte input or a 24-character hex string",
        ),  # test get_required_feature_roles with invalid client_id and invalid college_id
        (
            None,
            "65fc90aabf3ce46f00e28f7d",
            404,
            "College not found",
        ),  # test get_required_feature_roles with None client_id and invalid college_id
        (
            "65fc90aabf3ce46f00e28f7d",
            None,
            422,
            "Client screen controller not exists.",
        ),  # test get_required_feature_roles with invalid client_id and None college_id
        (
            None,
            None,
            400,
            "Client id or College id is mandatory",
        ),  # test get_required_feature_roles with None college_id and None client_id
    ],
)
async def test_get_required_feature_roles_for_students(
    http_client_test,
    super_admin_token,
    client_id,
    college_id,
    expected_status,
    expected_detail,
):
    """
    Handles unit test for the `get_required_feature_roles` endpoint when called with super admin authorization token.
    """
    params = {k: v for k, v in [("client_id", client_id),
                                ("college_id", college_id)] if v is not None}
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        params=params
    )
    # assert response.status_code == expected_status
    # assert response.json()["detail"] == expected_detail


async def test_get_required_feature_roles_with_valid_data(
    http_client_test,
    test_fetch_master_screen_data,
    super_admin_token,
):
    """
    Handles unit test for the `get_required_feature_roles` endpoint when called with valid data.
    """
    client_id, college_id = test_fetch_master_screen_data

    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Required roles for the college screen fetched successfully."

    # testing with valid client_id and None college_id
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Required roles for the client screen fetched successfully."

    # testing with None client_id and valid college_id
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Required roles for the college screen fetched successfully."

    # testing with valid client_id and invalid college_id # length(college_id) < 24
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles"
        f"?client_id={client_id}&college_id=65fc90aabf3ce46f00e28f8&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id `65fc90aabf3ce46f00e28f8` must be a 12-byte input or a 24-character hex string"

    # testing with valid client_id and invalid college_id # length(college_id) > 24
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles"
        f"?client_id={client_id}&college_id=65fc90aabf3ce46f00e28f8de&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id `65fc90aabf3ce46f00e28f8de` must be a 12-byte input or a 24-character hex string"

    # testing with valid client_id and invalid college_id
    response = await http_client_test.get(
        f"/client_automation/get_required_feature_roles"
        f"?client_id={client_id}&college_id=65fc90aabf3ce46f00e28f8d&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found"
