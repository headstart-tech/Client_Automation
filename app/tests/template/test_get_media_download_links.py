"""
This file contains the test cases of getting template gallery download links.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_download_template_gallery_unauthenticated(
    http_client_test
):
    """
    Unauthenticated user
    """
    response = await http_client_test.post(f"/templates/download_media?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_download_template_gallery_wrong_token(
    http_client_test
):
    """
    Wrong token
    """
    response = await http_client_test.post(
        f"/templates/download_media?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_download_template_gallery_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/templates/download_media"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_download_template_gallery_authorized_token(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    authorized token
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_gallery.delete_many({})
    await DatabaseConfiguration().template_gallery.insert_one({
        "uploaded_by": "apollo@example.com",
        "file_name": "DSCF2607.jpg",
        "file_type": "Image",
        "file_size": 9.733144760131836,
        "media_url": "https://sample-url.com",
        "dimensions": [
            6240,
            4160
        ],
        "is_deleted": False,
        "file_extension": ".jpg"
    })
    gallery = await DatabaseConfiguration().template_gallery.find_one({})
    response = await http_client_test.post(
        f"/templates/download_media"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(gallery.get('_id'))]
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template gallery download link retrieve successfully!!"


@pytest.mark.asyncio
async def test_download_template_gallery_authorized_token_with_wrong_media_id(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    authorized token
    """
    response = await http_client_test.post(
        f"/templates/download_media"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["123456789012345678901234"]
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid media selected."



@pytest.mark.asyncio
async def test_download_template_gallery_invalid_media_id(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    invalid media id
    """
    response = await http_client_test.post(
        f"/templates/download_media"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["1234567"]
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid media id"
