import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_list_of_all_colleges(http_client_test, setup_module,
                                college_super_admin_access_token,
                                test_college_validation):
    """
    Test cases for the list of all colleges

    Params:
        - http_client_test: Fixture returning AsyncClient object for API testing.
        - setup_module: Fixture setting up necessary DB data before tests.
        - college_super_admin_access_token: Fixture returning college super admin's access token.
        - test_college_validation: Fixture ensuring college exists and returns test college data.

    Assertions:
        - Response status code and JSON message.
    """

    # Not authenticated request
    response = await http_client_test.get(
        f"/client_automation/list_of_all_colleges?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.get(
        f"/client_automation/list_of_all_colleges?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """Test case with invalid page size (zero or negative)."""
    response = await http_client_test.get(
        f"/client_automation/list_of_all_colleges?pageSize=0&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


    """Test case with a very large page size (e.g., 1000)."""
    response = await http_client_test.get(
        f"/client_automation/list_of_all_colleges?pageSize=1000&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert len(response.json().get("data", [])) <= 1000

    """Test case with minimum allowed page size (1)."""
    response = await http_client_test.get(
        f"/client_automation/list_of_all_colleges?pageSize=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert len(response.json().get("data", [])) == 1