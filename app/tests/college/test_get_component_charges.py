"""
This file contains test cases related to get component charges
"""
import pytest


@pytest.mark.asyncio
async def test_get_component_charges(http_client_test, setup_module, test_component_charges_validation):
    """
    Get component charges
    """
    response = await http_client_test.get(f"/college/get_component_charges/")
    assert response.status_code == 200
    assert response.json()['message'] == "Get component charges."
