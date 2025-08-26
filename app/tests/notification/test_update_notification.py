"""
This file contains test cases for update notification by notification id or user id
"""
import pytest


@pytest.mark.asyncio
async def test_update_notification_invalid_id(http_client_test, test_college_validation, setup_module):
    """
    Invalid id for update notification
    """
    response = await http_client_test.put(
        f"/notifications/update/?notification_id=1234567890&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 422
    assert (
            response.json()["detail"]
            == "Notification id must be a 12-byte input or a 24-character hex string"
    )


@pytest.mark.asyncio
async def test_update_notification_invalid_user_id(http_client_test, test_college_validation, setup_module):
    """
    Invalid user id for update notification
    """
    response = await http_client_test.put(
        f"/notifications/update/?user_email=wrong_email&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_update_notification_wrong_id(http_client_test, test_college_validation, setup_module):
    """
    Wrong id for update notification
    """
    response = await http_client_test.put(
        f"/notifications/update/?notification_id=123456789012345678901234&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found."


@pytest.mark.asyncio
async def test_update_notification_by_id(
        http_client_test, test_college_validation, setup_module, notification_details
):
    """
    Update notification by id
    """
    response = await http_client_test.put(
        f"/notifications/update/?notification_id={str(notification_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Notification status updated."}


@pytest.mark.asyncio
async def test_update_notifications_by_user_id(
        http_client_test, test_college_validation, setup_module, notification_details, test_user_validation
):
    """
    Update user notifications by user id
    """
    response = await http_client_test.put(
        f"/notifications/update/?notification_id={notification_details.get('_id')}&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Notification status updated."}


@pytest.mark.asyncio
async def test_update_notification_required_parameter(http_client_test, test_college_validation, setup_module):
    """
    Required parameter for update notification
    """
    response = await http_client_test.put(
        f"/notifications/update/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 422
    assert response.json()["detail"] == "Need to pass notification id or user email."
