import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_fetch_list_of_all_fields(http_client_test, access_token, college_super_admin_access_token, setup_module,
                                               test_college_validation, test_super_admin_validation):
    """
    Test case for retrieving all client/college fields dynamically.
    """

    # Not authenticated request
    response = await http_client_test.get("/client_student_dashboard/fetch_list_of_all_fields")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.get(
        f"/client_student_dashboard/fetch_list_of_all_fields?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Missing client_id or college_id
    response = await http_client_test.get(
        f"/client_student_dashboard/fetch_list_of_all_fields?pageNum=1&pageSize=5&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Either clientId or collegeId must be provided"

    # Successful request using college_id
    college_id = str(test_college_validation.get("_id"))
    response = await http_client_test.get(
        "/client_student_dashboard/fetch_list_of_all_fields"
        f"?pageNum=1&pageSize=5&collegeId={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, dict)
    assert "data" in json_response
    assert "total" in json_response
    assert "count" in json_response
    assert "pagination" in json_response
    assert json_response["message"] == "Data fetched successfully"

    # Successful request using client_id
    client_id = str(test_college_validation.get("_id"))
    response = await http_client_test.get(
        "/client_student_dashboard/fetch_list_of_all_fields"
        f"?pageNum=1&pageSize=5&clientId={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, dict)
    assert "data" in json_response
    assert "total" in json_response
    assert "count" in json_response
    assert "pagination" in json_response
    assert json_response["message"] == "Data fetched successfully"

