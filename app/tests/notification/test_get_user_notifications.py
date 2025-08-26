"""
This file contains test cases for get user notifications
"""
import pytest


@pytest.mark.asyncio
async def test_get_user_notifications_required_page_number(
        http_client_test, test_college_validation, setup_module
):
    """
    Required page number for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/1234567890/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Num must be required and valid."


@pytest.mark.asyncio
async def test_get_user_notifications_required_page_size(
        http_client_test, test_college_validation, setup_module
):
    """
    Required page size for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/1234567890/?page_num=1&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Size must be required and valid."


@pytest.mark.asyncio
async def test_get_user_notifications_invalid_user_email(
        http_client_test, test_college_validation, setup_module
):
    """
    Invalid user email for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/wrong_email/?page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_user_notifications(
        http_client_test, test_college_validation, setup_module, notification_details, test_user_validation
):
    """
    Get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get users notifications."
    assert response.json()["pagination"]["previous"] is None
    # assert len(response.json()["data"]) == 1
    # Test response data
    for data in response.json()["data"]:
        assert data["notification_id"] == str(notification_details.get("_id"))
        assert data["student_id"] == str(notification_details.get("student_id"))
        assert data["application_id"] == str(notification_details.get("application_id"))
        assert data["message"] == notification_details.get("message")
        assert data["mark_as_read"] is False


@pytest.mark.asyncio
async def test_get_user_notifications_by_query_parameter(
        http_client_test, test_college_validation, setup_module, notification_details, test_user_validation
):
    """
    Test getting user notifications with query parameters.
    """
    # Test with different query parameter values
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=1&page_size=10&college_id={str(test_college_validation.get('_id'))}&unread_notification=true"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get users notifications."
    # assert len(response.json()["data"]) == 1
    assert response.json()["pagination"]["previous"] is None

    # Test response data
    for data in response.json()["data"]:
        assert data["notification_id"] == str(notification_details.get("_id"))
        assert data["student_id"] == str(notification_details.get("student_id"))
        assert data["application_id"] == str(notification_details.get("application_id"))
        assert data["message"] == notification_details.get("message")
        assert data["mark_as_read"] is False


@pytest.mark.asyncio
async def test_get_user_notifications_required_college_id(
        http_client_test, setup_module, notification_details, test_user_validation
):
    """
    Required college id for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=1&page_size=1"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "College Id must be required and valid."


@pytest.mark.asyncio
async def test_get_user_notifications_for_page_2(
        http_client_test, test_college_validation, setup_module, notification_details, test_user_validation
):
    """
    Get user notifications for page 2
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=2&page_size=1&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get users notifications."
    assert response.json()["pagination"]["next"] is None
    assert len(response.json()["data"]) == 0


@pytest.mark.asyncio
async def test_get_user_notifications_by_wrong_college_id_length(
        http_client_test, setup_module, notification_details, test_user_validation
):
    """
    Wrong college id length for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=1&page_size=1&college_id=1234567890"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input or a 24-character hex string"


@pytest.mark.asyncio
async def test_get_user_notifications_by_wrong_college_id(
        http_client_test, setup_module, notification_details, test_user_validation
):
    """
    Wrong college id for get user notifications
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=1&page_size=1&college_id=123456789012345678901234"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."


@pytest.mark.asyncio
async def test_get_user_notifications_for_page_3(
        http_client_test, test_college_validation, setup_module, notification_details, test_user_validation
):
    """
    Get user notifications for page 3
    """
    response = await http_client_test.get(
        f"/notifications/{test_user_validation.get('user_name')}/?page_num=3&page_size=1&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get users notifications."
    assert response.json()["pagination"]["next"] is None
    assert len(response.json()["data"]) == 0
