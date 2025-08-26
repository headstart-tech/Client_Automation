"""
This file contains test cases related to Exclusion list top header
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_top_header(http_client_test, setup_module,
                              college_super_admin_access_token, access_token,
                              test_college_validation, test_super_admin_validation):
    """
     Test cases to get header for Exclusion list
    """
    # Not authenticated
    response = await http_client_test.get(
        f"/exclusion_list/header_details?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.get(
        f"/exclusion_list/header_details?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id
    response = await http_client_test.get(
        f"/exclusion_list/header_details?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Not enough permissions
    response = await http_client_test.get(
        f"/exclusion_list/header_details"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Invalid college id
    response = await http_client_test.get(
        f"/exclusion_list/header_details"
        f"?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id
    response = await http_client_test.get(
        f"/exclusion_list/header_details"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    response = await http_client_test.get(
        f"/exclusion_list/header_details"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Return Exclusion list header details"
    assert all(key in response.json()["data"] for key in ["excluded", "current_excluded", "resumed", "email_excluded",
                                                  "whatsapp_excluded"])
