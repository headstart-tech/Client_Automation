"""
This file contains test cases for assign multiple applications to one counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_multiple_application_to_one_counselor_not_authentication(
        http_client_test, test_college_validation, setup_module, test_counselor_validation, application_details
):
    """
    Not authentication for assign multiple applications to one counselor
    """
    response = await http_client_test.put(
        f"/counselor/multiple_application_to_one_counselor?"
        f"counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"},
        json={
            "application_id": [str(application_details.get('_id'))]
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_multiple_application_to_one_counselor_wrong_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    Wrong id for assign multiple applications to one counselor
    """
    response = await http_client_test.put(
        f"/counselor/multiple_application_to_one_counselor?"
        f"counselor_id=12345678901234567890&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "application_id": [str(application_details.get('_id'))]
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "counselor not found"


@pytest.mark.asyncio
async def test_multiple_application_to_one_counselor_wrong_app_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    wrong application id for assign multiple applications to one counselor
    """
    response = await http_client_test.put(
        f"/counselor/multiple_application_to_one_counselor?"
        f"counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": ["1234567890123456789012"]},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == '1234567890123456789012 application_id not found'


@pytest.mark.asyncio
async def test_multiple_application_to_one_counselor(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation, application_details
):
    """
    Assign multiple applications to one counselor
    """
    response = await http_client_test.put(
        f"/counselor/multiple_application_to_one_counselor?"
        f"counselor_id={str(test_counselor_validation.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "application_id": [str(application_details.get('_id'))]
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data update successfully"
