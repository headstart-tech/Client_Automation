"""
This file contains test cases regarding for create student mapped
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_student_mapped_not_authenticated(http_client_test,
                                                test_college_validation,
                                                setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/data_segment/student_mapped"
        f"?data_segment_id=7736776"
        f"&page_num=1&page_size=25&feature_key={feature_key}"
        f"&college_id={test_college_validation.get('_id')}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_student_mapped_bad_credentials(
        http_client_test,
        test_create_data_segment_helper,
        test_college_validation,
        setup_module):
    """
    Bad token for data segment header view
    """
    response = await http_client_test.put(
        f"/data_segment/student_mapped"
        f"?data_segment_id=6419544432534e90f95eb402"
        f"&page_num=1&page_size=25&feature_key={feature_key}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_student_mapped_field_required(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_create_data_segment_helper
):
    """
    Field required for data segment header view
    """
    response = await http_client_test.put(
        f"/data_segment/student_mapped"
        f"?page_num=1&page_size=25&feature_key={feature_key}"
        f"&college_id={test_college_validation.get('_id')}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "data_segment_id or token is required"}


@pytest.mark.asyncio
async def test_student_mapped_invalid_id(
        http_client_test,
        test_create_data_segment_helper,
        test_college_validation,
        college_super_admin_access_token,
        setup_module):
    """
    data segment header view invalid id
    """
    response = await http_client_test.put(
        f"/data_segment/student_mapped"
        f"?data_segment_id=6419544432534e90f95eb40"
        f"&page_num=1&page_size=25&feature_key={feature_key}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (f"data segment id"
                                         f" `6419544432534e90f95eb40`"
                                         f" must be a 12-byte input or a "
                                         f"24-character hex string")
