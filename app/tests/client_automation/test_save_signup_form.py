import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_save_signup_form(http_client_test, setup_module,
                                college_super_admin_access_token,
                                test_college_validation, test_signup_form):
    """
    Test cases for the save_signup_form API.

    Params:
        - http_client_test: Fixture returning AsyncClient object for API testing.
        - setup_module: Fixture setting up necessary DB data before tests.
        - college_super_admin_access_token: Fixture returning college super admin's access token.
        - test_college_validation: Fixture ensuring college exists and returns test college data.

    Assertions:
        - Response status code and JSON message.
    """

    # Not authenticated request
    response = await http_client_test.post(
        f"/client_automation/save_signup_form/{str(test_college_validation.get('_id'))}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/client_automation/save_signup_form/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # To save fields Successfully
    response = await http_client_test.post(
        f"/client_automation/save_signup_form/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_signup_form
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Signup form fields saved successfully"


