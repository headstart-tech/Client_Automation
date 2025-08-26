"""
This file contains test cases related to publisher only API routes/endpoints
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
    leads_csv = PurePath(root_folder_path, Path(rf"sample_upload_publisher_leads.csv"))
    return leads_csv


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_publisher_parsing_error(http_client_test, test_college_validation,
                                                                 setup_module):
    """
    Parsing the body error when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/publisher/add_leads_using_json_or_csv/{str(test_college_validation.get('_id'))}/"
        f"?feature_key={feature_key}",
        headers={"Content-Type": "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_add_leads_using_json_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/publisher/add_leads_using_json_or_csv/628dfd41ef796e8f757a5c13/?feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_leads_using_json_bad_credentials(http_client_test, setup_module):
    """
    Bad token for add leads using json or csv
    """
    response = await http_client_test.post(
        f"/publisher/add_leads_using_json_or_csv/628dfd41ef796e8f757a5c13/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_publisher_file_required(
        http_client_test, publisher_access_token, setup_module, test_college_validation
):
    """
    File required when try to upload leads data using csv
    """
    response = await http_client_test.post(
        f"/publisher/add_leads_using_json_or_csv/{test_college_validation.get('_id')}/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File must be required and valid."}


@pytest.mark.asyncio
async def test_add_leads_using_json_no_permission(
        http_client_test, access_token, setup_module
):
    """
    No permission for leads using json or csv
    """
    response = await http_client_test.post(
        f"/publisher/add_leads_using_json_or_csv/628dfd41ef796e8f757a5c13/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_publisher_college_not_found(
        http_client_test, publisher_access_token, setup_module
):
    """
    College not found when try to upload leads data using csv
    """
    with open(f"{get_file_path()}", "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/publisher/add_leads_using_json_or_csv/123456789012345678901234/?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {publisher_access_token}"},
            files=files
        )
    assert response.status_code == 404
    assert response.json() == {'detail': 'College not found.'}


@pytest.mark.asyncio
async def test_upload_leads_using_csv_by_publisher_invalid_college_id(
        http_client_test, publisher_access_token, setup_module
):
    """
    College not found when try to upload leads data using csv
    """
    with open(f"{get_file_path()}", "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/publisher/add_leads_using_json_or_csv/12345678901234567890/?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {publisher_access_token}"},
            files=files
        )
    assert response.status_code == 422
    assert response.json() == {'detail': "Invalid college id."}


# Todo - following commented test cases not working correctly when run all test cases.
#  Otherwise working fine.
# @pytest.mark.asyncio
# async def test_upload_leads_using_csv_by_publisher(
#         http_client_test, publisher_access_token, setup_module, test_user_publisher_validation
# ):
#     """
#     Upload leads data using csv by publisher
#     :return:
#     """
#     with open(f"{get_file_path()}", "rb") as f:
#         files = {"file": f}
#         response = await http_client_test.post(
#             f"/publisher/add_leads_using_json_or_csv/{str(test_user_publisher_validation.get('associated_colleges', [])[0])}/",
#             headers={"Authorization": f"Bearer {publisher_access_token}"},
#             files=files
#         )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Received Request will be processed in the background once finished you "
#                                           "will receive an email. Data processing might take anywhere between 2 min -"
#                                           " 1 hour depending on the data volume."}


# @pytest.mark.asyncio
# async def test_upload_leads_using_csv_by_publisher_limit_exceed(
#         http_client_test, publisher_access_token, setup_module, test_offline_data,
#         test_user_publisher_validation
# ):
#     """
#     Upload leads data using csv by publisher exceed limit
#     :return:
#     """
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().lead_upload_history.delete_many({})
#     test_offline_data['imported_by'] = test_user_publisher_validation.get("_id")
#     await DatabaseConfiguration().lead_upload_history.insert_one(test_offline_data)
#     with open(f"{get_file_path()}", "rb") as f:
#         files = {"file": f}
#         response = await http_client_test.post(
#             f"/publisher/add_leads_using_json_or_csv/{str(test_user_publisher_validation.get('associated_colleges', [])[0])}/",
#             headers={"Authorization": f"Bearer {publisher_access_token}"},
#             files=files
#         )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "You have reached maximum limit of per day for upload leads."}


@pytest.mark.asyncio
async def test_get_all_leads_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_leads_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get publisher leads data
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_leads_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    No permission for get publisher leads data
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_all_leads(
        http_client_test, test_college_validation, publisher_access_token, setup_module
):
    """
    Get publisher leads data
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name',
                   'custom_application_id', 'student_email_id',
                   "course_name", 'student_mobile_no', 'payment_status',
                   'utm_medium', 'utm_campaign']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_leads_with_query_parameter(
        http_client_test, test_college_validation, publisher_access_token, setup_module
):
    """
    Get publisher leads data with query parameter
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?source_type=primary&lead_type=online&page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name',
                   'custom_application_id', 'student_email_id',
                   "course_name", 'student_mobile_no', 'payment_status',
                   'utm_medium', 'utm_campaign']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_leads_with_column_utm_medium_and_campaign(
        http_client_test, test_college_validation, publisher_access_token, setup_module
):
    """
    Get publisher leads data with column named utm medium and utm_campaign
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name',
                   'custom_application_id', 'student_email_id',
                   "course_name", 'student_mobile_no', 'payment_status',
                   'utm_medium', 'utm_campaign']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_leads_required_college_id(http_client_test, test_college_validation, publisher_access_token):
    """
    Required college id for get publisher leads data
    """
    response = await http_client_test.post(f"/publisher/get_all_leads/?page_num=1&page_size=1"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {publisher_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_get_all_leads_invalid_college_id(http_client_test, test_college_validation, publisher_access_token):
    """
    Invalid college id for get publisher leads data
    """
    response = await http_client_test.post(f"/publisher/get_all_leads/?college_id=1234567890"
                                           f"&page_num=1&page_size=1&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {publisher_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_all_leads_college_not_found(http_client_test, test_college_validation, publisher_access_token):
    """
    College not found for get publisher leads data
    """
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?college_id=123456789012345678901234&page_num=1&page_size=1"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_all_leads_no_found(
        http_client_test, test_college_validation, publisher_access_token, setup_module
):
    """
    Publisher leads data not found when try to get leads
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    response = await http_client_test.post(
        f"/publisher/get_all_leads/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()[
               "message"] == "Applications data fetched successfully!"
    # assert response.json()["data"] == []
    # assert response.json()["total"] == 0
    assert response.json()["count"] == 25
    # assert response.json()["pagination"]['next'] is None
    # assert response.json()["pagination"]['previous'] is None
