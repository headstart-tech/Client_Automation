"""
This file contains test cases regarding login student
"""
import pytest


@pytest.mark.asyncio
async def test_create_new_role(http_client_test, setup_module):
    """
    Different scenarios of test cases for create new role
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().role_collection.delete_one({"role_name": "string"})
    # Create new role
    response = await http_client_test.post(
        "/create_role/", json={"role_name": "string"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "New role created successfully."

    # Role name already exist
    response = await http_client_test.post(
        "/create_role/", json={"role_name": "string"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Role name 'string' already exist."
