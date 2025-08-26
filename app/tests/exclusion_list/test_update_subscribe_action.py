"""
This file contains test cases related to update subscribe status
"""
import datetime

import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_unsubscribe_status(http_client_test, setup_module,
                              college_super_admin_access_token, access_token, test_student_validation,
                              test_college_validation, test_super_admin_validation):
    """
     Test cases to update unsubscribe status
    """
    json = [str(test_student_validation.get("_id"))]
    status = "Resume"
    # Not authenticated
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status?action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Not enough permissions
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status?action={status}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=json
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Invalid college id
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status"
        f"?college_id=123&action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status"
        f"?college_id=123456789012345678901234&action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Invalid student id
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status"
        f"?college_id={str(test_college_validation.get('_id'))}&action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["12345"]
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Students not found: ['12345'] not found"

    # Wrong student id
    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status"
        f"?college_id={str(test_college_validation.get('_id'))}&action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["123456789012345678901234"]
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Students not found: ['123456789012345678901234'] not found"

    response = await http_client_test.post(
        f"/exclusion_list/update_subscribe_status"
        f"?college_id={str(test_college_validation.get('_id'))}&action={status}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    json = json
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Updated Successfully!"
    from app.database.configuration import DatabaseConfiguration
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one({"_id": ObjectId(test_student_validation.get("_id"))})
    assert student.get("unsubscribe", {}).get("value") == False
