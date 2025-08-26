"""
This file contains test cases regarding for add_data_segment_student
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_data_segment_student_not_authenticated(
        http_client_test,
        test_college_validation,
        application_details,
        setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/data_segment/add_data_segment_student"
        f"?data_segment_id=7736776"
        f"&college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        json=[str(application_details.get('_id'))]
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_data_segment_student_bad_credentials(
        http_client_test,
        test_create_data_segment_helper,
        test_college_validation,
        application_details,
        setup_module):
    """
    Bad token for data segment header view
    """
    response = await http_client_test.post(
        f"/data_segment/add_data_segment_student"
        f"?data_segment_id=6419544432534e90f95eb402"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=[str(application_details.get('_id'))]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_data_segment_student_field_required(
        http_client_test, test_college_validation,
        access_token, setup_module,
        application_details,
        test_create_data_segment_helper
):
    """
    Field required for data segment header view
    """
    response = await http_client_test.post(
        f"/data_segment/add_data_segment_student"
        f"?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=[str(application_details.get('_id'))]
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Data Segment Id must"
                                         " be required and valid."}


@pytest.mark.asyncio
async def test_add_data_segment_student_invalid_id(
        http_client_test,
        test_create_data_segment_helper,
        test_college_validation,
        application_details,
        college_super_admin_access_token,
        setup_module):
    """
    data segment header view invalid id
    """
    response = await http_client_test.post(
        f"/data_segment/add_data_segment_student"
        f"?data_segment_id=6419544432534e90f95eb40"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(application_details.get('_id'))]
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (f"Data Segment"
                                         f" `6419544432534e90f95eb40` must be"
                                         f" a 12-byte input or a 24-character"
                                         f" hex string")


async def test_add_data_segment_student_invalid_application_id(
        http_client_test, test_college_validation,
        test_create_data_segment_helper,
        college_super_admin_access_token, setup_module,
        application_details
):
    """
    Field required for data segment header view
    """
    response = await http_client_test.post(
        f"/data_segment/add_data_segment_student"
        f"?data_segment_id={str(test_create_data_segment_helper.get('_id'))}"
        f"&college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["6419544432534e90f95eb40"]
    )
    assert response.status_code == 422
    if test_create_data_segment_helper.get("module_name",
                                           "").lower() == "lead":
        assert response.json()["detail"] == (f"Student"
                                             f" `6419544432534e90f95eb40` "
                                             f"must be"
                                             f" a 12-byte input or a "
                                             f"24-character"
                                             f" hex string")
    else:
        assert response.json()["detail"] == (f"Application"
                                             f" `6419544432534e90f95eb40` "
                                             f"must be"
                                             f" a 12-byte input or a "
                                             f"24-character"
                                             f" hex string")
