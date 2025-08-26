"""
This file contains test cases regarding for get/download lead stage count
summary information.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_lead_stage_count_summary_info(
        http_client_test, test_college_validation, access_token,
        college_super_admin_access_token, followup_details, setup_module,
        start_end_date, test_source_data):
    """
    Test cases regarding for get/download lead stage count summary information.
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get lead stage count summary info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # College id required for get lead stage count summary info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required "
                                         "and valid."}

    # No permission for get lead stage count summary info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Get lead stage count info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "College id must be a 12-byte input or a "
                      "24-character hex string"}

    # College not found for get lead stage count summary info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Get lead stage count summary info.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get the lead stage count summary " \
                                         "information."
    assert "lead_stage" in response.json()['data'][0]
    assert "total" in response.json()['data'][0]

    # Get lead stage count summary info with date_range.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"date_range": start_end_date}
    )
    assert response.status_code == 200

    # Get lead stage count summary info with filter source name.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"source_names": [
            test_source_data.get("primary_source", {}).get("utm_source")]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get the lead stage count summary " \
                                         "information."
    assert "lead_stage" in response.json()['data'][0]
    assert "total" in response.json()['data'][0]

    # Download lead stage count summary info with filter source name.
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?download_data=true"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"source_names": [
            test_source_data.get("primary_source", {}).get("utm_source")]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "File downloaded successfully."
    assert "file_url" in response.json()

    # Lead stage count summary info data not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().leadsFollowUp.delete_many({})
    response = await http_client_test.post(
        f"/counselor/lead_stage_count_summary/?download_data=true"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"source_names": [
            test_source_data.get("primary_source", {}).get("utm_source")]}
    )
    assert response.status_code == 200
    assert response.json() == {"data": [],
                               "message": "Lead stage data not found."}
