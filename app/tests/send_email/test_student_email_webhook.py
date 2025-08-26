"""
This file contains test cases regarding API routes/endpoints related to update status of email based on message id
"""
import pytest


@pytest.mark.asyncio
async def test_update_email_status_required_body(http_client_test, setup_module):
    """
    Required message id for update email status
    """
    response = await http_client_test.post("/email/webhook/")
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."


@pytest.mark.asyncio
async def test_update_email_status(http_client_test, setup_module):
    """
    Update email status, testing purpose - we are passing wrong message id
    """
    response = await http_client_test.post("/email/webhook/",
                                           json={"message_id": "5481541", "event_type": "Open"})
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_update_email_status_massege_id(http_client_test, setup_module):
    """
    Update email status, testing purpose - empty_mail id
    """
    response = await http_client_test.post("/email/webhook/",
                                           json={})
    assert response.status_code == 400
    assert response.json()['detail'] == "Message Id must be required and valid."
