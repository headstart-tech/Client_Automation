"""
This file contains the test cases of add media for template gallery
"""

import pytest
from app.tests.admin.test_admin import get_file_path
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_template_media_header_unauthenticated(
    http_client_test
):
    """
    Unauthenticated user
    """
    response = await http_client_test.post(f"/templates/gallery_upload?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_add_template_media_wrong_token(
    http_client_test
):
    """
    Wrong token
    """
    response = await http_client_test.post(
        f"/templates/gallery_upload?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_template_media_invalid_college_id(
    http_client_test, access_token, setup_module
):
    """
    invalid college id
    """
    response = await http_client_test.post(
        f"/templates/gallery_upload"
        f"?college_id="
        f"1234567&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}



@pytest.mark.asyncio
async def test_add_template_media_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/templates/gallery_upload"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_add_template_media_authorized_token(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    authorized token
    """
    with open(get_file_path()['test_jpg'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/templates/gallery_upload"
            f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully!!"


@pytest.mark.asyncio
async def test_add_template_media_valid_pdf(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Valid pdf upload
    """
    with open(get_file_path()['test_docs'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/templates/gallery_upload?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully!!"


@pytest.mark.asyncio
async def test_add_template_media_valid_video(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Valid pdf upload
    """
    with open(get_file_path()['sample_small_video'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/templates/gallery_upload?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully!!"


@pytest.mark.asyncio
async def test_add_template_media_invalid_format_file(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Invalid file upload
    """
    with open(get_file_path()['college_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/templates/gallery_upload?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "file format is not supported"

