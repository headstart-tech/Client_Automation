"""
This file contains test cases related to get signup form extra fields
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_signup_form_extra_fields_required_field(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> required field for get signup form extra fields
    """
    response = await http_client_test.get(
        f"/college/signup_form_extra_fields/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}


@pytest.mark.asyncio
async def test_get_signup_form_extra_fields_invalid_college_id(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> invalid college id for get signup form extra fields
    """
    response = await http_client_test.get(
        f"/college/signup_form_extra_fields/?college_id=123456789&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_signup_form_extra_fields_incorrect_college_id(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> incorrect college id for get signup form extra fields
    """
    response = await http_client_test.get(
        f"/college/signup_form_extra_fields/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}


@pytest.mark.asyncio
async def test_get_signup_form_extra_fields_invalid_domain_url(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> invalid domain url for get signup form extra fields
    """
    response = await http_client_test.get(
        f"/college/signup_form_extra_fields/?domain_url=https://gfc.com&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}

#TODO: Need to update the testcase according to the updated API.

# @pytest.mark.asyncio
# async def test_get_signup_form_extra_fields(
#         http_client_test, super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Test case -> Get signup form extra fields
#     """
#     fields = ["college_id", "college_logo", "background_image", "student_dashboard_design_layout",
#               "admin_dashboard_design_layout", "extra_fields"]
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().college_form_details.update_one(
#         {"college_id": test_college_validation.get('_id')},
#         {'$unset': {
#             'form_details.student_registration_form_fields': True
#         }},
#     )
#     await DatabaseConfiguration().college_collection.update_one(
#         {"_id": test_college_validation.get('_id')},
#         {'$unset': {
#             "dashboard_domain": True
#         }}
#     )
#
#     # Signup form extra fields not found by college_id
#     response = await http_client_test.get(
#         "/college/signup_form_extra_fields/"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get signup form extra fields."
#     assert response.json()['data']['extra_fields'] == []
#     for field in fields:
#         assert field in response.json()["data"]
#
#     # Signup form extra fields not found by domain url
#     response = await http_client_test.get(
#         "/college/signup_form_extra_fields/"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get signup form extra fields."
#     assert response.json()['data']['extra_fields'] == []
#     for field in fields:
#         assert field in response.json()["data"]
#
#     await DatabaseConfiguration().college_form_details.update_one(
#         {"college_id": test_college_validation.get('_id')},
#         {'$set': {
#             'form_details.student_registration_form_fields': [
#                 {
#                     "field_name": "Test", "field_type": "select",
#                     "is_mandatory": True, "editable": False,
#                     "can_remove": False, "extra_field": True
#                 }
#             ]
#         }},
#         upsert=True
#     )
#     await DatabaseConfiguration().college_collection.update_one(
#         {"_id": test_college_validation.get('_id')},
#         {'$set': {
#             "dashboard_domain": "https://test.com"
#         }}
#     )
#
#     # Get signup form extra fields by college_id
#     response = await http_client_test.get(
#         "/college/signup_form_extra_fields/"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get signup form extra fields."
#     for field in fields:
#         assert field in response.json()["data"]
#
#     # Get signup form extra fields not found by domain url
#     response = await http_client_test.get(
#         f"/college/signup_form_extra_fields/?domain_url=https://test.com&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get signup form extra fields."
#     for field in fields:
#         assert field in response.json()["data"]
