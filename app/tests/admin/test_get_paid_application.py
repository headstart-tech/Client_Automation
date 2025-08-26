"""
This file contains test cases related to API route/endpoint for get all
paid application details.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_cases_of_get_paid_applications(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, super_admin_access_token,
        test_student_validation, application_details
        ):
    """
    Different test cases of get all paid applications.

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
        super_admin_access_token: A fixture which create super admin if not exist
            and return access token for super admin.
        test_student_validation: A fixture which create student if not exist
            and return student data.
        application_details: A fixture which add application add if not exist
            and return application data.

    Assertions:\n
        response status code and json message.
    """
    # Check authentication send wrong token
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    columns = ['application_id', 'student_id', 'student_name',
               'custom_application_id', 'student_email_id',
               "course_name", 'student_mobile_no', 'payment_status',
               "verification", "twelve_marks_name"]

    # Check state_code filter
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"state": {
            "state_code": [
                test_student_validation['address_details'][
                    'communication_address']['state']['state_code']]}})
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data" \
                                         " fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

    # Check city name filter
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"city": {
            "city_name": [test_student_validation['address_details'][
                              'communication_address']['city']['city_name']]}})
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data " \
                                         "fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

    # Check lead name filter
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"lead_stage": {"lead_b": False,"lead_name": [{"name": ["Fresh  Lead"], "label":[]}]}})
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data " \
                                         "fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

    # No permission for get all paid applications
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Get all paid applications by season wise
    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": ObjectId(str(application_details.get("_id")))},
        {"$set": {"payment_info": {"status": "captured"}}})
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data " \
                                         "fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        for column in columns:
            assert column in response.json()["data"][0]

        # Get all applications with column utm_medium and utm_campaign
        response = await http_client_test.post(
            f"/admin/all_paid_applications/?page_num=1&page_size=1&"
            f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={
                "Authorization": f"Bearer {college_super_admin_access_token}"},
            json={"utm_medium_b": True, "utm_campaign_b": True}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Applications data" \
                                             " fetched successfully!"
        assert response.json()["data"] is not None
        if response.json()["data"]:
            columns = ['application_id', 'student_id', 'student_name',
                       'custom_application_id', 'student_email_id',
                       "course_name", 'student_mobile_no', 'payment_status',
                       'utm_medium', 'utm_campaign', "verification",
                       "twelve_marks_name"]
            for column in columns:
                assert column in response.json()["data"][0]

    # Data not found when try to get all paid applications by season wise
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.delete_many({})
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Applications data " \
                                         "fetched successfully!"
    assert response.json()["data"] == []
    assert response.json()["pagination"]["next"] is None

    # Required college id for get all paid applications
    response = await http_client_test.post(f"/admin/all_paid_applications/?"
                                           f"page_num=1&page_size=1&feature_key={feature_key}",
                                           headers={
                                               "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be ' \
                                        'required and valid.'

    # Invalid college id for get all paid applications
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?college_id=1234567890&"
        f"page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found for get all paid applications
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?college_id=123456789012345678901234&"
        f"page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
