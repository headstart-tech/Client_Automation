"""
This file contains test cases related to get utm campaign list.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_utm_campaign_data(http_client_test, setup_module, test_college_validation,
                                     college_super_admin_access_token, access_token, test_student_data,
                                     test_student_validation):
    """
    Different test cases of get utm campaign list.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
            after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - access_token: A fixture which create student if not exist and return access token of student.
        - test_student_data: A fixture which return student dummy data.
        - test_student_validation: A fixture which create student if not exist
            and return student data.

    Assertions:\n
        response status code and json message.
    """
    utm_source = test_student_data.get("utm_source")
    utm_medium = test_student_data.get("utm_medium")
    payload = [{"source_name": utm_source, "utm_medium": utm_medium}]

    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/college/get_utm_campaign/?feature_key={feature_key}", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get utm campaign list.
    response = await http_client_test.post(f"/college/get_utm_campaign/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for get utm campaign list.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=payload
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Not found when try to get utm campaign list.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[{"source_name": "xyz", "utm_medium": "xyz"}])
    assert response.status_code == 200
    response_info = response.json()
    assert response_info['message'] == "Get utm campaign data."
    assert response_info['data'] == []

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": test_student_validation.get('_id')},
        {'$set': {'source': {"primary_source": {"utm_source": utm_source, "utm_medium": utm_medium,
                                                "utm_campaign": "test"}}}})

    # # Get utm campaign list.
    # response = await http_client_test.post(
    #     f"/college/get_utm_campaign/?feature_key={feature_key}"
    #     f"?college_id={str(test_college_validation.get('_id'))}",
    #     headers={
    #         "Authorization": f"Bearer {college_super_admin_access_token}"}, json=payload)
    # assert response.status_code == 200
    # response_info = response.json()
    # assert response_info['message'] == "Get utm campaign data."
    # response_data = response_info['data'][0]
    # for key in ["label", "value", "role"]:
    #     assert key in response_data

    # Wrong college id for get utm campaign list.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id=12345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=payload)
    assert response.status_code == 422
    assert response.json()[
               'detail'] == ("College id must be a 12-byte input "
                             "or a 24-character hex string")

    # College not found for get utm campaign list.
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=payload)
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college id for get utm medium data by source names
    response = await http_client_test.post(
        f"/college/get_utm_campaign/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}, json=payload)
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and valid."
