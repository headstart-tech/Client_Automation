"""
This file contains test cases related to update check-in status from telephony
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_check_in_status_not_authenticated(
    http_client_test
):
    #  user tried to update data not authenticated
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_check_in_status_wrong_access_token(
    http_client_test, setup_module
):
    # Pass invalid access token for update
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_check_in_status_blank_college_id(
    http_client_test, setup_module,
    college_counselor_access_token
):
    # Required college id for update
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_counselor_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}
    

@pytest.mark.asyncio
async def test_check_in_status_invalid_college_id(
    http_client_test, test_college_validation, setup_module,
    college_counselor_access_token
):
    # Invalid college id for update
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_counselor_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_check_in_status_wrong_college_id(
    http_client_test, test_college_validation, setup_module,
    college_counselor_access_token
):
    # Wrong college id for update
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_counselor_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_check_in_status_body_missing(
    http_client_test, test_college_validation, setup_module,
    college_counselor_access_token
):
    # Required body for update
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_counselor_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}
    

@pytest.mark.asyncio
async def test_check_in_status_missing_data_of_required_field(
    http_client_test, test_college_validation, setup_module,
    college_counselor_access_token
):

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().check_in_out_log.delete_many({})

    # update with missing data of required field.
    response = await http_client_test.post(
        f"/telephony/check_in_or_out?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_counselor_access_token}"},
        json={
            "check_in_status": False,
            "reason": {
                "title": "string",
                "icon": "string"
            }
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Check-in status update successfully."}
