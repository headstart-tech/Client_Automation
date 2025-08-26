"""
This file contains test cases of change default scholarship of applicant API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_change_default_scholarship(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        application_details, test_scholarship_validation):
    """
    Different test cases of change default scholarship of applicant.

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
        application_details: A fixture which add application add if not exist
            and return application data.
        test_scholarship_validation: A fixture which create scholarship if not exist
            and return scholarship data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')

    # Not authenticated for change default scholarship of applicant.
    response = await http_client_test.post(f"/scholarship/change_default_scholarship/?college_id={college_id}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # Required application id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required and valid."}

    obj_application_id = application_details.get("_id")
    application_id = str(obj_application_id)

    # No permission for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"application_id": application_id}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    scholarship_id = str(test_scholarship_validation.get('_id'))

    async def validate_common_successful_response(temp_response, temp_scholarship_id, custom_scholarship=False):
        assert temp_response.status_code == 200
        assert temp_response.json() == {"message": "Default scholarship changed."}
        temp_application_details = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)})
        if custom_scholarship:
            offered_scholarship_info = temp_application_details.get("offered_scholarship_info", {}).get("custom_scholarship_info")
            assert temp_scholarship_id == str(offered_scholarship_info.get("scholarship_id"))
        else:
            offered_scholarship_info = temp_application_details.get("offered_scholarship_info", {})
            assert temp_scholarship_id == str(offered_scholarship_info.get("default_scholarship_id"))
            assert temp_scholarship_id == str(
                offered_scholarship_info.get("all_scholarship_info", [])[0].get("scholarship_id"))

    # Change default scholarship of applicant by provide custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "set_custom_scholarship": True, "waiver_type": "Percentage",
              "waiver_value": 20, "description": "test"}
    )
    custom_scholarship = await DatabaseConfiguration().scholarship_collection.find_one(
        {"name": "Custom scholarship"})
    await validate_common_successful_response(response, str(custom_scholarship.get("_id")), custom_scholarship=True)

    custom_scholarship = await DatabaseConfiguration().scholarship_collection.find_one(
        {"name": "Custom scholarship"})
    await validate_common_successful_response(response, str(custom_scholarship.get("_id")), custom_scholarship=True)

    # Change default scholarship of applicant by scholarship id.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": scholarship_id}
    )
    await validate_common_successful_response(response, scholarship_id)

    # No passed waiver type/wave when change default scholarship of applicant by provide custom scholarsip.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "set_custom_scholarship": True}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Scholarship waiver type and value are mandatory when set custom scholarship "
                                         "as default scholarship."}

    # Invalid college id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": scholarship_id}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": scholarship_id}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": scholarship_id}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Invalid application id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": "123", "default_scholarship_id": scholarship_id}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Value error, Application Id must be required and valid."

    # Wrong application id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": "123456789012345678901234", "default_scholarship_id": scholarship_id}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Application not found id: 123456789012345678901234"

    # Invalid scholarship id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": "123"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Value error, Default Scholarship Id must be required and valid."

    # Wrong scholarship id for change default scholarship of applicant.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "default_scholarship_id": "123456789012345678901234"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Scholarship not found id: 123456789012345678901234"

    # Invalid percentage value Change default scholarship of applicant by provide custom scholarship.
    response = await http_client_test.post(
        f"/scholarship/change_default_scholarship/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"application_id": application_id, "set_custom_scholarship": True, "waiver_type": "Percentage",
              "waiver_value": 101, "description": "test"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Custom scholarship percentage should be less than or equal to 100."}
