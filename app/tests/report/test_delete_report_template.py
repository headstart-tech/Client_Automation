"""
This file contains test cases related to delete report template
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_report_template_unauthorized(
    http_client_test, setup_module,
    college_super_admin_access_token
):
    # Un-authorized user tried to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_delete_report_template_invalid_user(
        http_client_test, setup_module,
        college_super_admin_access_token
):
    # Pass invalid access token to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_delete_report_template_required_college_id(
        http_client_test, setup_module,
        college_super_admin_access_token
):
    # Required college id to delete report tmeplate
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

@pytest.mark.asyncio
async def test_delete_report_template_invalid_college_id(
        http_client_test, setup_module,
        college_super_admin_access_token, test_report_template_data
):
    # Invalid college id to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json= [str(test_report_template_data.get('_id'))]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

@pytest.mark.asyncio
async def test_delete_report_template_college_not_found(
        http_client_test, setup_module,
        college_super_admin_access_token, test_report_template_data
):
    # Wrong college id to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json= [str(test_report_template_data.get('_id'))]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

@pytest.mark.asyncio
async def test_delete_report_template(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_report_template_data
):
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json= [str(test_report_template_data.get('_id'))]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Reports deleted successfully."}

@pytest.mark.asyncio
async def test_delete_report_template_invalid_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token
):

    # Invalid id to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json= ["12345"]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Report id `12345` must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_delete_report_template_not_found_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token
):
    # Wrong id to delete report template
    response = await http_client_test.post(
        f"/reports/delete_report_by_id/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json= ["659d04d6e05a95f8ee00ff23", "659d04d6e05a95f8ee00ff22"]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Make sure provided report ids are correct."}