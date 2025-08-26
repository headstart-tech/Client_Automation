"""
This file contains test cases for total student queries
"""
import pytest

from app.tests.conftest import access_token
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_student_total_queires_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_student_total_queires_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get student total queires
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_student_total_queires_required_page_num(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for get total student querires
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?"
        f"college_id={str(test_college_validation.get('_id'))}&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_student_total_queires_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for get student total queires
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?page_num=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_student_total_queires_required_college_id(http_client_test, test_college_validation,
                                                        college_super_admin_access_token):
    """
    Required college id for get all applications
    """
    response = await http_client_test.post(f"/admin/student_total_queries/?page_num=1&page_size=1&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_student_total_queires_invalid_college_id(http_client_test, test_college_validation,
                                                       college_super_admin_access_token):
    """
    Invalid college id for get all applications
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_student_total_queires_college_not_found(http_client_test, test_college_validation,
                                                      college_super_admin_access_token):
    """
    College not found for get all applications
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?college_id=123456789012345678901234&page_num=1"
        f"&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_student_total_queires_for_1st_page(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    Get all applications
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get student queries."


@pytest.mark.asyncio
async def test_student_total_queires_no_data_for_page(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    no data found for get all applications
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?page_num=441&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get student queries."
    assert response.json()["data"] == []
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_student_total_queires_by_season_wise(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date,
        application_details
):
    """
    Get all applications by season wise
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Get student queries."


@pytest.mark.asyncio
async def test_student_total_queires_by_season_wise_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    No found data for get all applications by season wise
    """
    response = await http_client_test.post(
        f"/admin/student_total_queries/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Get student queries."
    assert response.json()["pagination"]["next"] is None
