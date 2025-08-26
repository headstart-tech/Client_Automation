import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_color_theme(http_client_test, college_super_admin_access_token, test_college_validation):
    """
    Test case for retrieving the color theme of a college.
    """
    college_id = str(test_college_validation.get("_id"))

    # 1. Valid request - College with color theme
    response = await http_client_test.get(
        f"/client_automation/get_color_theme/{college_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "color_theme" in response.json()

    # 2. Non-existent college ID (invalid)
    non_existent_college_id = "64f5b10a87d94f001e5a1234"
    response = await http_client_test.get(
        f"/client_automation/get_color_theme/{non_existent_college_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found"

    # 3. Invalid ObjectId format
    invalid_college_id = "invalid_id_format"
    response = await http_client_test.get(
        f"/client_automation/get_color_theme/{invalid_college_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid college_id format"
