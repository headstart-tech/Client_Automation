
"""
This file contains test cases of give custom scholarship API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_give_custom_scholarship(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        application_details, test_template_validation):
    """
    Different test cases of give custom scholarship.

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
        access_token: A fixture which create student if not exist and return access token of student.
        application_details: A fixture which create application if not exist and return application details.
        test_template_validation: A fixture which create template if not exist and return template details.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')
    # Not authenticated for give custom scholarship.
    response = await http_client_test.post(f"/scholarship/give_custom_scholarship/"
                                           f"?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required application_ids for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # Invalid application_ids for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": ["123"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Value error, Application Id `123` must be a 12-byte input or a "
                                         "24-character hex string"}

    application_id = str(application_details.get("_id"))

    # Required waiver_type for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Waiver Type must be required and valid."}

    # Invalid waiver_type for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Waiver Type must be required and valid."}

    # Required waiver_value for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Waiver Value must be required and valid."}

    # Invalid waiver_value for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 0}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Waiver Value must be required and valid."}

    # Required template_id for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Id must be required and valid."}

    # Invalid template_id for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": "123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Value error, Template Id must be required and valid."}

    template_id = str(test_template_validation.get("_id"))
    # No permission for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": template_id}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 1,
              "template_id": template_id}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Custom scholarship given to applicants."}

    # Give custom scholarship by invalid application id.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": ["123456789012345678901234"], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": template_id}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Application not found id: 123456789012345678901234"

    # Give custom scholarship by invalid template id.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": "123456789012345678901234"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Template not found id: 123456789012345678901234"

    # Invalid college id for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": template_id}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": template_id}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when give custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/give_custom_scholarship/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_ids": [application_id], "waiver_type": "Percentage", "waiver_value": 20,
              "template_id": template_id}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}
