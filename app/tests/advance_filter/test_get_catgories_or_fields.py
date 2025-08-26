"""
This file contains test cases related to API route/endpoint for get advance
filter categories/fields.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo - we'll cover all possible test cases like filter test cases later on
@pytest.mark.asyncio
async def test_cases_of_get_advance_filter_categories_or_fields(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, super_admin_access_token,
        access_token
        ):
    """
    Different test cases of get advance filter categories/fields.

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

    Assertions:\n
        response status code and json message.
    """
    # Check authentication send wrong token
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get('_id'))
    # Wrong token for advance filter categories
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for advance filter categories
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Get advance filter categories
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().advance_filter_field_collection.delete_one(
        {"college_id": test_college_validation.get("_id")})
    # Data not found when try to get advance filter categories
    from app.database.configuration import DatabaseConfiguration
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?page_num=1&page_size=1&"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Get the advance filter categories."
    assert response.json()["data"] == []

    await DatabaseConfiguration().advance_filter_field_collection.insert_one(
        {"college_id": test_college_validation.get("_id"), "Student Details":
            [{"field_name": "test", "operators": ["Equal", "Not equal"],
              "field_type": "text"}]})
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Get the advance filter categories."
    assert response.json()["total"] is not None
    assert "Student Details" in response.json()["data"]

    # Required college id for advance filter categories
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be ' \
                                        'required and valid.'

    # Invalid college id for advance filter categories
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?college_id=1234567890&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found for advance filter categories
    response = await http_client_test.get(
        f"/advance_filter/categories_or_fields/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
