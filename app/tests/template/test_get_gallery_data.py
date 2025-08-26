"""
This file contains the test cases of getting template gallery data.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_template_gallery_unauthenticated(
    http_client_test
):
    """
    Unauthenticated user
    """
    response = await http_client_test.post(f"/templates/get_media_gallery?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_template_gallery_wrong_token(
    http_client_test
):
    """
    Wrong token
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_template_gallery_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_template_gallery_authorized_token(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    authorized token
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template gallery data retrieve successfully!!"


@pytest.mark.asyncio
async def test_template_gallery_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_template_gallery_invalid_college_id(
    http_client_test, access_token, setup_module
):
    """
    invalid college id
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id="
        f"123456&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_template_gallery_invalid_quick_filter(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    invalid quick filter
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "media_type": ["INVALID"]
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid media type."}


@pytest.mark.asyncio
async def test_template_gallery_valid_quick_filter(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    invalid quick filter
    """
    response = await http_client_test.post(
        f"/templates/get_media_gallery"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "media_type": ["Video", 'File']
        }
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Template gallery data retrieve successfully!!"
