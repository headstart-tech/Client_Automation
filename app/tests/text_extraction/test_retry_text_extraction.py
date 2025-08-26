import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_retry_text_extraction_not_authenticated(
        http_client_test,test_student_validation, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student/documents/retry_extraction/?student_id={str(test_student_validation.get('_id'))}"
        f"&feature_key={feature_key}"
        f"&doc_type=tenth&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_retry_text_extraction_bad_credentials(
        http_client_test,test_student_validation, test_college_validation, setup_module
):
    """
    Bad token to retry
    """
    response = await http_client_test.get(
        f"/student/documents/retry_extraction/?student_id={str(test_student_validation.get('_id'))}"
        f"&feature_key={feature_key}"
        f"&doc_type=tenth&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer wrong"},)

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_retry_text_extraction_college_id_field_required(
        http_client_test,test_student_validation, test_college_validation, setup_module, access_token
):
    """
    required college id
    """
    response = await http_client_test.get(
        f"/student/documents/retry_extraction/?student_id={str(test_student_validation.get('_id'))}"
        f"&doc_type=tenth&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},)

    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_retry_text_extraction_student_id_field_required(
        http_client_test,test_student_validation, test_college_validation,
        setup_module, college_super_admin_access_token
):
    """
    required student id
    """

    response = await http_client_test.get(
            f"/student/documents/retry_extraction/?"
            f"doc_type=tenth&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization":  f"Bearer {college_super_admin_access_token}"},)
    assert response.status_code == 400
    assert response.json() == {"detail": "Student Id must be required and valid."}
