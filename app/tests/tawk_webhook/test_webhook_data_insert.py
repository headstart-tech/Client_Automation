"""
This file contains test cases related to create data from the tawk webhook.
"""
import pytest


@pytest.mark.asyncio
async def test_webhook_tawk_with_invalid_college_id(
    http_client_test, setup_module
):
    #  user tried to create chat data with invalid college id.
    response = await http_client_test.post(
        "/tawk/webhook?college_id=2"
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                               "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_webhook_tawk_without_college_id(
    http_client_test, setup_module
):
    #  user tried to create chat data without college id.
    response = await http_client_test.post(
        "/tawk/webhook"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}


@pytest.mark.asyncio
async def test_webhook_tawk_wrong_college_id(
    http_client_test, setup_module
):
    #  user tried to create chat data wrong college id.
    response = await http_client_test.post(
        "/tawk/webhook?college_id="
        f"123456789012345678901234",
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_webhook_tawk_payload_not_passed(
    http_client_test, test_college_validation, setup_module
):
    #  user tried to create chat data payload not passed.
    response = await http_client_test.post(
        "/tawk/webhook?college_id="
        f"{str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Verification failed"}

