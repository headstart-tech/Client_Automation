"""
This file contains test cases related to API route/endpoint counselor
followup details summary information.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counselor_followup_details_summary(
        http_client_test, test_college_validation, access_token,
        college_counselor_access_token, setup_module
):
    """
    Test cases related to API route/endpoint counselor followup details
    summary information.
    """
    # Not authenticated for get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Bad token for get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == \
           {'detail': "College Id must be required and valid."}

    # Invalid college id for get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 422
    assert response.json() == \
           {'detail': "College id must be a 12-byte input or a 24-character "
                      "hex string"}

    # College not found for get followup details summary info
    response = await http_client_test.post(
        "/counselor/followup_details_summary/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 422
    assert response.json() == {'detail': "College not found."}

    # No permission for get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

    # Get followup details summary info
    response = await http_client_test.post(
        f"/counselor/followup_details_summary/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}
    )
    assert response.json()["message"] == "Get the counselor followup details."
    assert response.status_code == 200
    for key in ["total_followups", "today_followups", "upcoming_followups",
                "overdue_followups", "missed_calls", "connected_calls"]:
        assert key in response.json()["data"]
