"""
This file contains test cases regarding  download reports by ids.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_download_reports_by_ids(
        http_client_test, setup_module, test_college_validation, access_token,
        college_super_admin_access_token, test_report_validation
):
    """

    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/"
        f"?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for download report data by id (s)
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for download report data by id (s)
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."

    # Not enough permission for download report data by id (s)
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=["1234"]
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    from app.database.configuration import DatabaseConfiguration
    report = await DatabaseConfiguration().report_collection.find_one({})
    # Download report by report id
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=[str(report.get("_id"))]
    )
    assert response.status_code == 200

    # Required college id for download report by report id
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["1234"]
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for download report by report id
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/?college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["1234"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == \
           'College id must be a 12-byte input or a 24-character hex string'

    # College not found for download report by report id
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["1234"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Data not found for download report data by id (s)
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=[]
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "No any report data found to download."

    # Invalid report id for download report data by id (s)
    response = await http_client_test.post(
        f"/reports/get_download_url_by_request_id/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["1234"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == \
           'Report id `1234` must be a 12-byte input or a 24-character ' \
           'hex string'
