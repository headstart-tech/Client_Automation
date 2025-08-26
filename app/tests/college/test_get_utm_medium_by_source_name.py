"""
This file contains test cases related to get utm medium data by source names
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_not_authenticated(
        http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/?feature_key={feature_key}", json=["test"])
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_bad_credentials(
        http_client_test, setup_module):
    """
    Bad token for get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=["test"]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names(
        http_client_test,
        college_super_admin_access_token,
        test_college_data,
        setup_module,
        test_college_validation,
        test_student_validation):
    """
    Get utm medium data by source names
    """
    # await DatabaseConfiguration().studentsPrimaryDetails.insert_one(
    #     {"_id": ObjectId(str(test_student_validation.get('_id'))),
    #      "source.primary_source": {"utm_source": "test",
    #                                "utm_medium": "test"}})
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["test"])
    assert response.status_code == 200
    assert response.json()['message'] == "Get utm medium data."


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_not_found(
        http_client_test,
        college_super_admin_access_token,
        test_college_data,
        setup_module,
        test_source_data,
        test_college_validation,
        test_student_validation):
    """
    Not found when try to get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[test_source_data.get("primary_source", {}).get("utm_source")])
    assert response.status_code == 200
    assert response.json()['message'] == "Get utm medium data."


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_wrong_college_id(
        http_client_test, college_super_admin_access_token,
        setup_module):
    """
    Wrong college id for get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/?college_id=12345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["test"])
    assert response.status_code == 422
    assert response.json()[
               'detail'] == ("College id must be a 12-byte input "
                             "or a 24-character hex string")


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_college_not_found(
        http_client_test, college_super_admin_access_token,
        setup_module):
    """
    College not found for get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["test"])
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."


@pytest.mark.asyncio
async def test_get_utm_medium_data_by_source_names_required_college_id(
        http_client_test,
        college_super_admin_access_token,
        setup_module):
    """
    Required college id for get utm medium data by source names
    """
    response = await http_client_test.post(
        f"/college/utm_medium_by_source_names/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["test"])
    assert response.status_code == 400
    assert response.json()[
               'detail'] == "College Id must be required and valid."
