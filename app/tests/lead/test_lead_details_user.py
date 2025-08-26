"""
This file contains test cases related to get lead details.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_lead_details(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, application_details):
    """
    Different test cases of get lead details.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        application_details: A fixture which add application add if not exist
            and return application data.

    Assertions:\n
        response status code and json message.
    """
    college_id = str(test_college_validation.get('_id'))
    app_id = str(application_details.get('_id'))

    # Not authenticated for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/{app_id}?college_id={college_id}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Invalid credentials for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/{app_id}?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Get lead details.
    # ToDo -  Following test case giving error when run all test cases,
    #  need to resolve it
    # response = await http_client_test.get(
    #     f"/lead/lead_details_user/{app_id}?college_id={college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    # )
    # assert response.status_code == 200
    # assert response.json()["message"] == "data fetch successfully"
    # data = response.json()["data"][0]
    # for item in ["lead_details", "additioan_details"]:
    #     assert item in data

    # Application not found for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/62a057ef1ec1188907d262a2?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    # Invalid application id for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/1234567890123456789012?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json()["detail"] == "Application id must be a 12-byte "
                                         "input or a 24-character hex string")

    # College not found for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/{app_id}?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Invalid college id for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/{app_id}?college_id=123456&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert (response.json()["detail"] == "College id must be a 12-byte "
                                         "input or a 24-character hex string")

    # Required college id for get lead details.
    response = await http_client_test.get(
        f"/lead/lead_details_user/{app_id}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert (response.json()["detail"] == "College Id must be required and "
                                         "valid.")
