
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_set_default_client_stages(http_client_test, setup_module, college_super_admin_access_token, college_counselor_access_token,
                                         test_college_validation):
    """
    Test case for setting default client stages.
    """
    # Not authenticated request
    response = await http_client_test.post(f"/client_student_dashboard/set_default_client_stages?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/client_student_dashboard/set_default_client_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Client ID not found for user
    response = await http_client_test.post(
        f"/client_student_dashboard/set_default_client_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client ID not found"

    # Successfully setting default client stages
    response = await http_client_test.post(
        f"/client_student_dashboard/set_default_client_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Default client stages set successfully"