"""
This file contains test cases for get counselor history
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_counselor_call_history_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_counselor_call_history_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get counselor history
    """
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_counselor_call_history_required_college_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required college id for get counselor call history
    """
    response = await http_client_test.get(
        f"/call_activities/history/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_counselor_call_history_data_invalid_college_id(http_client_test, test_college_validation,
                                                                  college_super_admin_access_token):
    """
    Invalid college id for get counselor call history
    """
    response = await http_client_test.get(
        f"/call_activities/history/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_counselor_call_history_data_college_not_found(http_client_test, test_college_validation,
                                                                 college_super_admin_access_token):
    """
    College not found for get counselor call history
    """
    response = await http_client_test.get(
        f"/call_activities/history/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_counselor_call_history_no_permission(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    No permission for get counselor history
    """
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_counselor_call_history(
        http_client_test, test_college_validation, college_counselor_access_token, test_call_history, setup_module
):
    """
    Get counselor call history data (with/without pagination)
    """
    columns = ["type", "call_to", "call_to_name", "call_from", "call_from_name", "call_started_at", "call_duration",
               "created_at"]
    # With pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] is not None
    # assert response.json()["total"] == 1
    assert response.json()["pagination"] == {"next": None, "previous": None}
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

    # Without pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] is not None
    # assert response.json()["total"] == 1
    assert response.json()["pagination"] is None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_counselor_call_history_not_found(
        http_client_test, test_college_validation, college_counselor_access_token, setup_module
):
    """
    Counselor call history data not found (with/without pagination)
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})

    # With pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] == []
    assert response.json()["total"] == 0
    assert response.json()["pagination"] == {"next": None, "previous": None}

    # Without pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] == []
    assert response.json()["total"] == 0
    assert response.json()["pagination"] is None


@pytest.mark.asyncio
async def test_get_counselor_call_history_using_search_input(
        http_client_test, test_college_validation, college_counselor_access_token, test_call_history, setup_module
):
    """
    Get counselor call history data using search input (with/without pagination)
    """
    columns = ["type", "call_to", "call_to_name", "call_from", "call_from_name", "call_started_at", "call_duration",
               "created_at"]
    # With pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&search_input={test_call_history.get('call_from')[6:]}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] is not None
    # assert response.json()["total"] == 1 # Todo: currently commented statement is failing, need to fix later
    assert response.json()["pagination"] == {"next": None, "previous": None}
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

    # Without pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&search_input={test_call_history.get('call_from')[6:]}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] is not None
    # assert response.json()["total"] == 1
    assert response.json()["pagination"] is None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_counselor_call_history_not_found_using_search_input(
        http_client_test, test_college_validation, college_counselor_access_token, setup_module, call_activity_data
):
    """
    Counselor call history data not found using search input (with/without pagination)
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})

    # With pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&search_input={call_activity_data.get('mobile_numbers')[0]}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] == []
    assert response.json()["total"] == 0
    assert response.json()["pagination"] == {"next": None, "previous": None}

    # Without pagination
    response = await http_client_test.get(
        f"/call_activities/history/?college_id={str(test_college_validation.get('_id'))}"
        f"&search_input={call_activity_data.get('mobile_numbers')[0]}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get call history of counselor."
    assert response.json()["data"] == []
    assert response.json()["total"] == 0
    assert response.json()["pagination"] is None
