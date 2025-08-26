"""
This file contains test cases related to get form details
"""
import pytest


@pytest.mark.asyncio
async def test_get_form_details(http_client_test, setup_module, test_form_details_validation):
    """
    Get component charges
    """
    response = await http_client_test.get(f"/college/get_form_details/")
    assert response.status_code == 200
    assert response.json()['message'] == "Get form details."
