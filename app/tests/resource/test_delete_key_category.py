"""
This file contains test cases related to delete key category.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_questions(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, access_token,
        test_key_category_validation, test_question_validation
):
    """
    Test cases for API route which useful for delete key category.
    """
    # Un-authorized user tried to delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    college_id = str(test_college_validation.get('_id'))

    # Required index number for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Index Number must be required and "
                                         "valid."}

    # No permission for delete key category.
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"{college_id}&index_number=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Delete a key category
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"{college_id}&index_number=0&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Key category deleted successfully."}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$unset': {'key_categories': True}})

    # Invalid index number for delete key category
    response = await http_client_test.delete(
        f"/resource/delete_key_category/?college_id="
        f"{college_id}&index_number=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Please provide a valid index number."
