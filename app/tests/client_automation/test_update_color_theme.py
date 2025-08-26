
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_update_color_theme(http_client_test, college_super_admin_access_token, test_college_validation):
    """
    Test case for updating the color theme of a college.
    """

    valid_payload = {
        "background": {
            "default": "#F9FAFC",
            "paper": "#FFFFFF"
        },
        "divider": {
            "default": "#B3D2E2"
        },
        "primary": {
            "main": "#C5A02F",
            "light": "#c5a02f",
            "dark": "#262401",
            "contrastText": "#FFFFFF",
            "sideBarButton": "#BFB895"
        },
        "text": {
            "default": "#121828",
            "primary": "#4E5417",
            "secondary": "#65748B",
            "disabled": "rgba(55, 65, 81, 0.48)",
            "contrastText": "#FFFFFF"
        },
        "neutral": {
            "100": "#F3F4F6",
            "200": "#E5E7EB",
            "300": "#D1D5DB",
            "400": "#9CA3AF",
            "500": "#6B7280",
            "600": "#4B5563",
            "700": "#374151",
            "800": "#1F2937",
            "900": "#111827"
        }
    }

    college_id = str(test_college_validation.get("_id"))

    # Not authenticated
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={college_id}&feature_key={feature_key}",
        json=valid_payload
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Invalid token
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json=valid_payload
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    # Valid request
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_payload
    )
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")

    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 200
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"}
    # )
    # assert response.status_code == 200
    # from app.database.configuration import DatabaseConfiguration
    # college = await DatabaseConfiguration().college_collection.find_one({"_id": ObjectId(college_id)})
    # assert college["color_theme"] == valid_payload

    # Non-existent college ID
    fake_college_id = "64f5b10a87d94f001e5a1234"
    response = await http_client_test.post(
        f"/client_automation/update_color_theme/?college_id={fake_college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_payload
    )
    assert response.status_code == 422
