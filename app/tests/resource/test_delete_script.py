"""
This file contains test cases related to delete script
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_scripts_unauthorized(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details, test_script_data
):
    """
    Test Cases of deleting a script
    """
    # Un-authorized user tried to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_delete_scripts_invalid_user(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, test_script_data
):
    # Pass invalid access token to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_delete_scripts_required_college_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, test_script_data
):
    # Required college id to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

@pytest.mark.asyncio
async def test_delete_scripts_invalid_college_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, test_script_data
):
    # Invalid college id to delete scripts
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?college_id="
        f"1234&script_id={str(test_script_data.get('id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

@pytest.mark.asyncio
async def test_delete_scripts_college_not_found(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, test_script_data
):
    # Wrong college id to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?college_id="
        f"123456789012345678901234&script_id={str(test_script_data.get('id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

@pytest.mark.asyncio
async def test_delete_scripts(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, test_script_data
):
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&script_id={str(test_script_data.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Script deleted successfully!"}

@pytest.mark.asyncio
async def test_delete_scripts_invalid_script_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token ,test_script_data
):

    # Invalid script id to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Script id `123` must be a 12-byte "
                                         "input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_delete_scripts_not_found_script_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token
):
    # Wrong script id to delete script
    response = await http_client_test.delete(
        f"/resource/delete_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Script not found id: 123456789012345678901234"}