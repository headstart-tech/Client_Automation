"""
This file contains the test cases of getting specific media fetch details api
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_media_spec_details_unauthenticated(
    http_client_test, setup_module
):
    """
    Unauthenticated user
    """
    response = await http_client_test.get(f"/templates/get_spec_media_details?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_media_spec_details_wrong_token(
    http_client_test, setup_module
):
    """
    Wrong token
    """
    response = await http_client_test.get(
        f"/templates/get_spec_media_details?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_media_spec_details_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.get(
        f"/templates/get_spec_media_details"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_media_spec_details_invalid_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.get(
        f"/templates/get_spec_media_details"
        f"?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_media_spec_details_wrong_payload(
    http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    authorized token
    """
    response = await http_client_test.get(
        f"/templates/get_spec_media_details"
        f"?college_id={str(test_college_validation.get('_id'))}"
        f"&media_id=12345678&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Gallery media id is invalid."


@pytest.mark.asyncio
async def test_media_spec_details_authorized_token(
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
    response = await http_client_test.get(
        f"/templates/get_spec_media_details"
        f"?college_id={str(test_college_validation.get('_id'))}"
        f"&media_id={str(gallery.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Media data fetched successfully."

