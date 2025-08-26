"""
This file contains test cases related to create key category.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_key_category(
    http_client_test,
    test_college_validation,
    setup_module,
    college_super_admin_access_token,
    application_details,
):
    """
    Test cases for API route which useful for create key category.
    """
    # Un-authorized user tried to create key category.
    response = await http_client_test.post(f"/resource/create_key_category/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and " "valid."}

    # Invalid college id for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "College id must be a 12-byte input " "or a 24-character hex string"
    }

    # Wrong college id for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    college_id = str(test_college_validation.get("_id"))
    # Required body for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and " "valid."}

    # Required category name for create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Category Name must be required and " "valid."}

    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get("_id")},
        {"$unset": {"key_categories": True}},
    )
    # Create key category.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"category_name": "test"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Key category successfully created."}

    # Key category already exist.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"category_name": "test"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": f"Key category `test` already exist."}

    # Invalid index when update key category name.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"category_name": "test1"},
    )
    assert response.status_code == 200
    # Todo: we will check later

    # assert response.json() == {"detail": "Please provide a valid index "
    #                                      "number."}

    # Update key category name.
    response = await http_client_test.post(
        f"/resource/create_key_category/?college_id=" f"{college_id}&index_number=0&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"category_name": "test1"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Key category name successfully " "updated."}
