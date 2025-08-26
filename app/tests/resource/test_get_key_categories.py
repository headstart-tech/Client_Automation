"""
This file contains test cases related to get key categories.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_key_categories(
    http_client_test,
    test_college_validation,
    setup_module,
    college_super_admin_access_token,
    test_key_category_validation,
):
    """
    Test cases for API route which useful for get key categories.
    """
    # Un-authorized user tried to get key categories.
    response = await http_client_test.get(f"/resource/get_key_categories/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for get key categories.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get key categories.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and " "valid."}

    # Invalid college id for get key categories.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?college_id=" f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "College id must be a 12-byte input " "or a 24-character hex string"
    }

    # Wrong college id for get key categories.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?college_id=" f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().questions.delete_many({})
    # Get key categories.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    # Todo: Check that the key categories are actually, will do later
    # assert response.json()["data"] == [{"category_name": "test", "total": 0,
    #                                     "index": 0}]

    DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get("_id")},
        {"$unset": {"key_categories": True}},
    )

    # Key categories not found.
    response = await http_client_test.get(
        f"/resource/get_key_categories/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the key categories."
    assert response.json()["data"] == []
