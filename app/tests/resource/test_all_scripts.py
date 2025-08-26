"""
This file contains test cases related to get all scripts
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_scripts(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    """
    Test Cases of get all sccripts
    """
    # Un-authorized user tried to create or update a script.
    response = await http_client_test.post(
        f"/resource/scripts/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for create or update a script.
    response = await http_client_test.post(
        f"/resource/scripts/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to get all scripts
    response = await http_client_test.post(
        f"/resource/scripts/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id to get all scripts
    response = await http_client_test.post(
        f"/resource/scripts/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id to get all scripts
    response = await http_client_test.post(
        f"/resource/scripts/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    #test case to get all scripts
    response = await http_client_test.post(
        f"/resource/scripts/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the scripts."

