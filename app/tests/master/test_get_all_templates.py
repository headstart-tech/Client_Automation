import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_templates(http_client_test, college_super_admin_access_token, setup_module, college_counselor_access_token,
                                         test_college_validation):
    """
    Test case for retrieving all application form templates.
    """

    # Not authenticated request
    response = await http_client_test.get(f"/master_stages/get_all_templates/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.get(
        f"/master_stages/get_all_templates/?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful retrieval of client stages
    response = await http_client_test.get(
        f"/master_stages/get_all_templates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)