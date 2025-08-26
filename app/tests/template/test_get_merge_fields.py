"""
This file contains test cases of get template merge fields.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_get_template_merge_fields_not_authenticated(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_template_merge_fields,
        access_token
):
    """
    Test cases for get template merge fields.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required "
                                         "and valid."}

    # Invalid college id for get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found for get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Get template merge fields.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the template merge fields."
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    assert response.json()["pagination"] == {}

    # Get template merge fields with pagination.
    response = await http_client_test.get(
        f"/templates/get_template_merge_fields/?"
        f"college_id={str(test_college_validation.get('_id'))}&page_num=1&"
        f"page_size=2&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the template merge fields."
    assert response.json()["total"] == 1
    assert response.json()["count"] == 2
    assert response.json()["pagination"] == {"previous": None, "next": None}
