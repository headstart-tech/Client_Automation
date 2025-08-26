"""
This file contains test cases related to templates for filter
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_templates_for_filter(http_client_test, setup_module,
                              college_super_admin_access_token, access_token,
                              test_college_validation, test_super_admin_validation):
    """
     Test cases
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter?template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required template type
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Template Type must be required and valid.'}

    # Not enough permissions
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter"
        f"?college_id={str(test_college_validation.get('_id'))}&template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Invalid college id
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter"
        f"?college_id=123&template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id
    response = await http_client_test.post(
        f"/templates/template_ids_for_filter"
        f"?college_id=123456789012345678901234&template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    response = await http_client_test.post(
        f"/templates/template_ids_for_filter"
        f"?college_id={str(test_college_validation.get('_id'))}&template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    if result:
        assert "template_id" in result[0]
