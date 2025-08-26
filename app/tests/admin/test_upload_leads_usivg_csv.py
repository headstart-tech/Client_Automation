"""
This file contains test cases related to upload leads by admin user
"""
import inspect
from pathlib import Path, PurePath

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

def get_file_path():
    """
    This function returns the absolute path of the file which required for test cases
    """
    file_path = Path(inspect.getfile(inspect.currentframe())).resolve()
    root_folder_path = PurePath(file_path).parent
    leads_csv = PurePath(root_folder_path, Path(rf"sample_leads.csv"))
    return leads_csv


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_parsing_error(http_client_test, test_college_validation, setup_module):
    """
    Parsing the body error when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Content-Type": "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_not_authenticated(http_client_test, test_college_validation,
                                                                setup_module):
    """
    Not authenticated when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_bad_token(http_client_test, test_college_validation, setup_module):
    """
    Bad token when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_field_required(
        http_client_test, access_token, setup_module
):
    """
    Field required when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_data_name_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Data name required when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Data Name must be required and "
                                         "valid."}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_file_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    File required when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/admin/add_leads_using_or_csv/?"
        f"college_id={test_college_validation.get('_id')}&data_name=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File must be required and valid."}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    No permission when try to upload leads data using csv
    """
    with open(get_file_path(), "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/add_leads_using_or_csv/?"
            f"college_id={test_college_validation.get('_id')}&data_name=test&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user_college_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    College not found when try to upload leads data using csv
    """
    with open(get_file_path(), "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            "/admin/add_leads_using_or_csv/?"
            "college_id=628dfd41ef796e8f757a5c11&data_name=test&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files,
        )
    assert response.status_code == 422
    assert response.json() == {'detail': 'College not found.'}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_user(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Upload leads data using csv by user
    :return:
    """
    with open(get_file_path(), "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/add_leads_using_or_csv/?"
            f"college_id={str(test_college_validation.get('_id'))}"
            f"&data_name=test&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            files=files,
        )
    assert response.status_code == 200
    assert response.json() == \
           {"message": "Received Request will be processed in the "
                       "background once finished you will receive an email. "
                       "Data processing might take anywhere between 2 min - "
                       "1 hour depending on the data volume."}
