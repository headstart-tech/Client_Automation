"""
This file contains test cases regarding API routes/endpoints related to update status of sms based on transaction id
"""
import pytest


@pytest.mark.asyncio
async def test_update_sms_status(http_client_test, setup_module):
    """
    Update sms status, testing purpose - we are passing wrong message id
    """
    response = await http_client_test.get("/sms/webhook/?txid=1")
    assert response.status_code == 200
    assert response.json() is None
