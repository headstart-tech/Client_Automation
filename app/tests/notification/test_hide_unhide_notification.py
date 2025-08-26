"""
This file contains test cases for hide/un-hide notification by notification id.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_hide_unhide_notification(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, access_token, notification_details):
    """
    Different test cases of hide/un-hide notification by notification id.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        access_token: A fixture which create student if not exist
            and return access token for student.
        notification_details: A fixture which useful for get notification data.

    Assertions:\n
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))

    # Check authentication by send wrong token.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?notification_id=1234567890&"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?notification_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert (response.json() ==
            {"detail": "College Id must be required and valid."})

    # Wrong college id for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json() ==
            {"detail": "College not found."})

    # Invalid college id for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json() ==
            {"detail": "College id must be a 12-byte input or a 24-character "
                       "hex string"})

    # Invalid notification id for update notification.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/"
        f"?notification_id=1234567890&"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (
            response.json()["detail"]
            == "Notification id `1234567890` must be a 12-byte input or a "
               "24-character hex string"
    )

    # Wrong notification id update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?notification_id="
        f"123456789012345678901234&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert (response.json() ==
            {"message": f"Either no permission to change hide status of "
                        f"notification or notification not found by "
                        f"id: 123456789012345678901234."})

    # Hide notification by id.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?"
        f"notification_id={str(notification_details.get('_id'))}&"
        f"hide=true&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": f"Notification hide successfully."}

    # Un-hide notification by id.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?notification_id="
        f"{str(notification_details.get('_id'))}&hide=false&"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Notification un-hide successfully."}

    # Required notification id for update notification hide status.
    response = await http_client_test.put(
        f"/notifications/hide_by_id/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Notification Id must be required "
                                         "and valid."}
