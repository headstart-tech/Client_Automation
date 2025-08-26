"""
This file contains test cases of get fee details.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_fee_details(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token):
    """
    Different test cases of get fee details.

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

    Assertions:\n
        response status code and json message.
    """
    # Test case -> not authenticated if user not logged in
    response = await http_client_test.post(
        f"/student_application/fee_details/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get("_id"))
    from app.database.configuration import DatabaseConfiguration
    # Test case -> bad token for change preference order
    response = await http_client_test.post(
        f"/student_application/fee_details/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Test case -> field `course_name` required for change
    # preference order
    response = await http_client_test.post(
        f"/student_application/fee_details/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Course Name must be required "
                                         "and valid."}

    # Test case -> field `preference_info` required for change
    # preference order
    response = await http_client_test.post(
        f"/student_application/fee_details/?"
        f"course_name=Test&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required "
                                         "and valid."}

    # Test case -> for change preference order
    response = await http_client_test.post(
        f"/student_application/fee_details/?"
        f"course_name=Test&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["Preference1"]
    )
    assert response.status_code == 200
    for item in ["total_fee", "preference_fee"]:
        assert item in response.json()

    # Test case -> Required college id for change preference order.
    response = await http_client_test.post(
        f"/student_application/fee_details/?course_name=Test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["Preference1"]
    )
    assert response.status_code == 400
    assert response.json()["detail"] == ("College Id must be required "
                                         "and valid.")

    # Test case -> Invalid college id for change preference order.
    response = await http_client_test.post(
        f"/student_application/fee_details/?"
        f"course_name=Test&college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["Preference1"]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Test case -> Wrong college id for change preference order.
    response = await http_client_test.post(
        f"/student_application/fee_details/?"
        f"course_name=Test&college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json=["Preference1"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
