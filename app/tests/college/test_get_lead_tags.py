"""
This file contains test cases related to get lead tags
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_lead_tags(
        http_client_test, test_college_validation, access_token,
        college_super_admin_access_token, setup_module):
    """
    Test cases for get lead tags
    """
    # Not authenticated if user not logged in
    response = await http_client_test.get(f"/college/lead_tags/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get lead tags
    response = await http_client_test.get(
        f"/college/lead_tags/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    college_id = str(test_college_validation.get('_id'))
    # No permission for get lead tags
    response = await http_client_test.get(
        f"/college/lead_tags/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Lead tags not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$unset': {'lead_tags': True}})
    response = await http_client_test.get(
        f"/college/lead_tags/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == "Lead tags not found."

    # Get lead tags
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {'lead_tags': ["test1", "test2"]}})
    response = await http_client_test.get(
        f"/college/lead_tags/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get the lead tags."

    # Wrong college id for get lead tags
    response = await http_client_test.get(
        f"/college/lead_tags/?college_id=12345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"

    # College not found for get lead tags
    response = await http_client_test.get(
        f"/college/lead_tags/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # required college id for get lead tags
    response = await http_client_test.get(
        f"/college/lead_tags/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and" \
                                        " valid."
