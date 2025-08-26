"""
This file contains test cases related to get top performing data segment details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/data_segments/communication_performance_dashboard/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_bad_credentials(http_client_test, setup_module):
    """
    Bad token for get top performing data segments details
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_required_college_id(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    Required college id for get top performing data segments details
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_required_communication_type(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    Required communication type for get top performing data segments details
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Communication Type must be required and valid."}


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for get top performing data segments details
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/"
        f"?college_id={str(test_college_validation.get('_id'))}&communication_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_by_wrong_college_id(http_client_test,
                                                                            college_super_admin_access_token,
                                                                            setup_module):
    """
    Get top performing data segments details by wrong college id
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?college_id=12345678901234"
        f"&communication_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"


@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_college_not_found(http_client_test,
                                                                          college_super_admin_access_token,
                                                                          setup_module):
    """
    College not found for get top performing data segments details
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?college_id=123456789012345678901234&communication_type"
        f"=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

@pytest.mark.asyncio
async def test_get_top_performing_data_segments_details_success(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module):
    """
    Successfully get top performing data segments details with valid inputs and permissions
    """
    response = await http_client_test.get(
        f"/data_segments/communication_performance_dashboard/?college_id={str(test_college_validation.get('_id'))}"
        f"&communication_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert 'data' in response_data
    assert 'message' in response_data
    assert response_data['message'] == "Get counselor wise call activity data."

    # Check the content of the 'data' field
    data_segments = response_data['data']
    assert isinstance(data_segments, list)

    if data_segments:
        for data_segment in data_segments:
            assert 'data_segment_id' in data_segment
            assert 'data_segment_name' in data_segment
            assert 'email_sent' in data_segment
            assert 'email_opened' in data_segment
            assert 'email_clicked' in data_segment
            assert 'open_rate' in data_segment
            assert 'click_rate' in data_segment
