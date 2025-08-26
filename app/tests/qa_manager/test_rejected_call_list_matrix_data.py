"""
Test case for all the rejected call data set in header section of QA manager.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_unauthenticated_get_data(
    http_client_test
):
    # Un-authorized user tried to use API.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_invalid_access_token(http_client_test):

    # Pass invalid access token for get the data from API.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_without_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Required college id.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}


@pytest.mark.asyncio
async def test_invalid_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Invalid college id.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}


@pytest.mark.asyncio
async def test_wrong_college_id(http_client_test, setup_module, college_super_admin_access_token):

    # Wrong college id.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_get_valid_data_set(http_client_test, setup_module, college_super_admin_access_token, test_college_validation):

    # Get the proper data set.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_valid_data_set_with_date_range(http_client_test,  setup_module, college_super_admin_access_token, test_college_validation):

    # Get the proper data set with date range.
    response = await http_client_test.post(
        f"/qa_manager/rejected_call_list_metrics/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "start_date": "2023-04-04",
            "end_date": "2023-05-06"
        }
    )
    assert response.status_code == 200
