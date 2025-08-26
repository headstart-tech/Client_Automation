"""
This file contains test cases of add call activity
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_call_activity_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_call_activity_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for add call activity
    """
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_call_activity_required_body(http_client_test, test_college_validation,
                                               college_counselor_access_token, setup_module):
    """
    Required body for add call activity
    """
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_add_call_activity_no_permission(http_client_test, test_college_validation, access_token,
                                               call_activity_data, setup_module):
    """
    No permission for add call activity
    """
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=call_activity_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_call_activity(http_client_test, test_college_validation, college_counselor_access_token,
                                 call_activity_data, setup_module):
    """
    Add call activity
    """
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=call_activity_data)
    assert response.status_code == 200
    assert response.json()['message'] == 'Call activities added.'


@pytest.mark.asyncio
async def test_add_call_activity_required_type(http_client_test, test_college_validation,
                                               college_counselor_access_token, call_activity_data,
                                               setup_module):
    """
    Required type for add call activity
    """
    call_activity_data.pop('type')
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=call_activity_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Type must be required and valid.'


@pytest.mark.asyncio
async def test_add_call_activity_required_mobile_numbers(http_client_test, test_college_validation,
                                                         college_counselor_access_token,
                                                         call_activity_data, setup_module):
    """
    Required mobile numbers for add call activity
    """
    call_activity_data.pop('mobile_numbers')
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=call_activity_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Mobile Numbers must be required and valid.'


@pytest.mark.asyncio
async def test_add_call_activity_required_call_started_datetimes(http_client_test, test_college_validation,
                                                                 college_counselor_access_token,
                                                                 call_activity_data, setup_module):
    """
    Required call started datetimes for add call activity
    """
    call_activity_data.pop('call_started_datetimes')
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=call_activity_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Call Started Datetimes must be required and valid.'


@pytest.mark.asyncio
async def test_add_call_activity_required_call_durations(http_client_test, test_college_validation,
                                                         college_counselor_access_token,
                                                         call_activity_data, setup_module):
    """
    Required call durations for add call activity
    """
    call_activity_data.pop('call_durations')
    response = await http_client_test.post(
        f"/call_activities/add/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=call_activity_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Call Durations must be required and valid.'
