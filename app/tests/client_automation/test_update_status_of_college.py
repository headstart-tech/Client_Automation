import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_status_of_college(http_client_test, setup_module,
                                college_super_admin_access_token,
                                test_college_validation, ):
    college_id = str(test_college_validation.get('_id'))


    # 1. Not authenticated request
    response = await http_client_test.post(f"/client_automation/update_status_of_college/?feature_key={feature_key}",
        params={"status": "Approved"},
        json={"college_ids": [college_id]}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # 2. Bad token
    response = await http_client_test.post(f"/client_automation/update_status_of_college/?feature_key={feature_key}",
        params={"status": "Approved"},
        json={"college_ids": [college_id]},
        headers={"Authorization": f"Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # 3. Missing college_ids (empty list)
    response = await http_client_test.post(f"/client_automation/update_status_of_college/?feature_key={feature_key}",
        params={"status": "Approved"},
        json={"college_ids": []},
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College IDs list cannot be empty."

    # 4. Valid request
    response = await http_client_test.post(f"/client_automation/update_status_of_college/?feature_key={feature_key}",
        params={"status": "Approved"},
        json={"college_ids": [college_id]},
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Approved"
    assert data["college_ids"] == [college_id]
    assert "Updated status for" in data["message"]