"""
This file contains test cases of get panel names
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_panel_names(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, access_token, test_panel_validation):
    """
    Different test cases of get panel names.
    """
    college_id = str(test_college_validation.get('_id'))

    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/planner/get_panel_names/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Wrong token for get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Required college id for get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?college_id=12&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found for get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # No permission for get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Get panel names
    response = await http_client_test.post(
        f"/planner/get_panel_names/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get panel names."
    for name in ["_id", "name"]:
        assert name in response.json()['data'][0]

    # No panel found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().panel_collection.delete_many({})
    response = await http_client_test.post(
        f"/planner/get_panel_names/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get panel names."
    assert response.json()["data"] == []
