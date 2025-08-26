"""
This file contains test cases related to get add or update component charges
"""
import pytest


@pytest.mark.asyncio
async def test_add_component_charges_required_field(http_client_test, setup_module, test_component_charges):
    """
    Get add or update component charges
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().component_charges_collection.delete_many({})
    response = await http_client_test.put(f"/college/component_charges/")
    assert response.status_code == 400
    assert response.json()['detail'] == "Body must be required and valid."


@pytest.mark.asyncio
async def test_add_component_charges(http_client_test, setup_module, test_component_charges):
    """
    Get add or update component charges
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().component_charges_collection.delete_many({})
    response = await http_client_test.put(f"/college/component_charges/", json=test_component_charges)
    assert response.status_code == 200
    assert response.json()['message'] == "Add component charges."


@pytest.mark.asyncio
async def test_update_component_charges(http_client_test, setup_module, test_component_charges,
                                        test_component_charges_validation):
    """
    Get add or update component charges
    """
    response = await http_client_test.put(f"/college/component_charges/", json=test_component_charges)
    assert response.status_code == 200
    assert response.json()['message'] == "Updated component charges."
