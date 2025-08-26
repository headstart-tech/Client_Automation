"""
This file contains test cases related to get existing field names with unique key_names
"""
import pytest


@pytest.mark.asyncio
async def test_get_field_names_with_unique_key_names(http_client_test, setup_module, test_form_details_validation):
    """
    Get existing field names with key_names
    """
    # Fields not exist in database
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().field_mapping_collection.delete_many({})
    response = await http_client_test.get(f"/college/existing_fields/")
    assert response.status_code == 200
    assert response.json()['message'] == "Get existing fields details."
    assert response.json()['data'] == []

    # Fields exists in database
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().field_mapping_collection.insert_one({"student_registration_form_fields": [
        {"field_name": "Your Full Name", "key_name": "full_name", "field_type": "text"}]})
    response = await http_client_test.get(f"/college/existing_fields/")
    assert response.json()['message'] == "Get existing fields details."
    assert response.json()['data'] == [{"field_name": "Your Full Name", "key_name": "full_name", "field_type": "text"}]
