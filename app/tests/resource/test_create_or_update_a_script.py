"""
This file contains test cases related to create or update a script.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_update_scripts_unauthenticated(
    http_client_test
):
    # Un-authorized user tried to create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_create_or_update_scripts_wrong_access_token(
    http_client_test
):
    # Pass invalid access token for create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_or_update_scripts_blank_college_id(
    http_client_test, setup_module,
    college_super_admin_access_token
):
    # Required college id for create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}
    

@pytest.mark.asyncio
async def test_create_or_update_scripts_invalid_college_id(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token
):
    # Invalid college id for create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_create_or_update_scripts_wrong_college_id(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token
):
    # Wrong college id for create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_create_or_update_scripts_body_missing(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token
):
    # Required body for create or update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}
    

@pytest.mark.asyncio
async def test_create_or_update_scripts_missing_data_of_required_field(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token
):

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scripts_details.delete_many({})

    # Create a script with missing data of required field.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "program_name": [{
                "course_name": "string",
                "course_id": "tgdvewdgdwdq87848t823h2vq",
                "specialization_name": "string"
            }],
            "source_name": [],
            "lead_stage": ["Interested", "Not Interested"],
            "tags": ["tech"],
            "application_stage": None
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Required fields has not passed."}


@pytest.mark.asyncio
async def test_create_or_update_scripts_create_script(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Create a script.
    data = {
        "script_name": "string",
        "program_name": [
            {
                "course_name": "string",
                "course_id": "tgdvewdgdwdq87848t823h2vq",
                "specialization_name": "string"
            }
        ],
        "source_name": [
            "string"
        ],
        "lead_stage": [],
        "tags": None,
        "application_stage": [
            "string"
        ],
        "script_text": "string",
        "save_or_draft": "save"
    }
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Script created successfully."}


@pytest.mark.asyncio
async def test_create_or_update_scripts_update_script(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token
):
    from app.database.configuration import DatabaseConfiguration
    # await DatabaseConfiguration().scripts_details.delete_many({})

    script = await DatabaseConfiguration().scripts_details.find_one({})

    # Update a script.
    update_data = {
        "program_name": [
            {
                "course_name": "string",
                "course_id": "tgdvewdgdwdq87848t823h2vq",
                "specialization_name": "string"
            }
        ],
        "source_name": [
            "string"
        ],
        "script_text": "string",
        "save_or_draft": "save"
    }
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id={str(script.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=update_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Script updated successfully."}


@pytest.mark.asyncio
async def test_create_or_update_scripts_nothing_to_update(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    # await DatabaseConfiguration().scripts_details.delete_many({})

    script = await DatabaseConfiguration().scripts_details.find_one({})
    # Unable to Update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id={str(script.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "There is nothing to update."}


@pytest.mark.asyncio
async def test_create_or_update_scripts_invalid_script_id_for_update(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    update_data = {
        "source_name": ['facebook', 'organic'],
        "tags": ["tech"]
    }
    # Invalid script id for update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=update_data
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Script id `123` must be a 12-byte "
                                         "input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_create_or_update_scripts_wrong_script_id_for_update(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    update_data = {
        "source_name": ['facebook', 'organic'],
        "tags": ["tech"]
    }
    # Wrong script id for update a script.
    response = await http_client_test.put(
        f"/resource/create_or_update_a_script/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"script_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=update_data
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Script not found by id: "
                                         "123456789012345678901234"}
