"""
This file contains test cases related to check in check out update status
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_status(http_client_test, setup_module, test_user_validation,
                              college_super_admin_access_token, access_token,
                              test_college_validation, test_super_admin_validation):
    """
     Test cases for update status
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/checkin_checkout/update_status?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Update Status
    response = await http_client_test.post(
        f"/checkin_checkout/update_status?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for Update Status
    response = await http_client_test.post(
        f"/checkin_checkout/update_status?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Invalid student id
    response = await http_client_test.post(
        f"/checkin_checkout/update_status"
        f"?college_id={str(test_college_validation.get('_id'))}&user_id={test_user_validation.get('_id')}"
        f"&action=CheckOut&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Invalid college id for Update Status
    response = await http_client_test.post(
        f"/checkin_checkout/update_status"
        f"?college_id=123&user_id={test_user_validation.get('_id')}&action=CheckOut&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for Update Status
    response = await http_client_test.post(
        f"/checkin_checkout/update_status"
        f"?college_id=123456789012345678901234&user_id={test_user_validation.get('_id')}&action=CheckOut"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    response = await http_client_test.post(
        f"/checkin_checkout/update_status"
        f"?college_id={str(test_college_validation.get('_id'))}&user_id={test_user_validation.get('_id')}"
        f"&action=CheckOut&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "User didn't Login yet!"
