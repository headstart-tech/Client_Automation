"""
This file contains test cases regarding to perform action on raw data leads
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_action_on_raw_data_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_action_on_raw_data_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_action_on_raw_data_required_college_id(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required college id for perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?feature_key={feature_key}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_action_on_raw_data_required_action(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required action for perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Action must be required and valid."}


@pytest.mark.asyncio
async def test_action_on_raw_data_required_payload(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required payload for perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&action=email"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_action_on_raw_data_required_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_action_payload_data
):
    """
    Required payload for perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&action=email"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=test_action_payload_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_action_on_raw_data_required_offline_ids(
        http_client_test, test_college_validation, access_token, setup_module, test_action_payload_data
):
    """
    Required offline ids for perform action on raw data leads
    """
    test_action_payload_data.pop("offline_ids")
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&action=email"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=test_action_payload_data
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Offline Ids must be required and valid."}


@pytest.mark.asyncio
async def test_action_on_raw_data(
        http_client_test, test_college_validation, super_admin_access_token, setup_module, test_action_payload_data
):
    """
    Perform action on raw data leads
    """
    response = await http_client_test.post(
        f"/manage/action_on_raw_data/?college_id={test_college_validation.get('_id')}&action=email"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=test_action_payload_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Performed action on raw data"}
