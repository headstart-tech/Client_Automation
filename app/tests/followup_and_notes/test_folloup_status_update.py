"""
this file contains all test case of followup status update
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_followup_status_update_not_authorization(
        http_client_test, application_details, setup_module, test_college_validation
):
    """
    this test case authenticate sending wrong token
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_followup_update_not_enough(
        http_client_test, super_admin_access_token, followup_details, setup_module, test_college_validation
):
    """
    authenticate except college_counselor and college_super_admin token
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/{str(followup_details.get('application_id'))}/"
        f"?status=true&index_number=0&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_followup_status_update(
        http_client_test, college_super_admin_access_token, followup_details, setup_module,
        test_college_validation
):
    """
    update status of followup status update
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/{str(followup_details.get('application_id'))}/"
        f"?status=true&index_number=0&testing=true&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "followup has updated"


@pytest.mark.asyncio
async def test_followup_update_status_wrong_type_id(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    checking wrong type application id
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/62a9b8774035e93c7ff24/"
        f"?status=true&index_number=0&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Application id must be a 12-byte input or a 24-character hex string."
    )


@pytest.mark.asyncio
async def test_followup_status_out_of_range_index(
        http_client_test, college_super_admin_access_token, followup_details, setup_module,
        test_college_validation
):
    """
    checking the out of range index number
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/{str(followup_details.get('application_id'))}"
        f"/?status=true&index_number=111&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "index number not found"
