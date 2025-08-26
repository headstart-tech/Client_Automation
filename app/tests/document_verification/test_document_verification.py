import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_application_details(http_client_test, test_college_validation, college_super_admin_access_token,
                                           setup_module):
    """
        test cases related to getting application of document verification
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/document_verification/all_applications/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # get applications providing page_num and page_size
    response = await http_client_test.post(
        f"/document_verification/all_applications/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

    # get document verification applications
    response = await http_client_test.post(
        f"/document_verification/all_applications/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert 'count' in response.json()
    assert 'data' in response.json()
    assert 'pagination' in response.json()
    assert 'total' in response.json()
    assert 'message' in response.json()

    # Bad token to get applications
    response = await http_client_test.post(
        f"/document_verification/all_applications/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id
    response = await http_client_test.post(
        f"/document_verification/all_applications/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # college not found
    response = await http_client_test.post(
        f"/document_verification/all_applications/?page_num=1&page_size=25"
        f"&college_id=765432189012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # invalid college id
    response = await http_client_test.post(
        f"/document_verification/all_applications/?page_num=1&page_size=25"
        f"&college_id=3214567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'
