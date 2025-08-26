"""
This file contains test cases of de-list applicants from scholarship API.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delist_applicants_from_scholarship_list(
        http_client_test, setup_module, test_college_validation, college_super_admin_access_token, access_token,
        test_scholarship_validation, application_details):
    """
    Different test cases of de-list applicants from scholarship.

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
        test_scholarship_validation: A fixture which create scholarship if not exist
            and return scholarship data.
        application_details: A fixture which add application add if not exist
            and return application data.

    Assertions:\n
        response status code and json message.
    """
    college_id = test_college_validation.get('_id')

    # Not authenticated for de-list applicants from scholarship.
    response = await http_client_test.post(f"/scholarship/delist_applicants/?college_id={college_id}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required scholarship_id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Scholarship Id must be required and valid."}

    scholarship_id = str(test_scholarship_validation.get('_id'))

    # Required body for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    application_id = str(application_details.get("_id"))

    # No permission for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=[application_id]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId

    # De-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "De-list applicants from scholarship list."}
    scholarship_info = await DatabaseConfiguration().scholarship_collection.find_one({
        "_id": test_scholarship_validation.get("_id")
    })
    assert ObjectId(application_id) not in scholarship_info.get("offered_applicants")
    assert ObjectId(application_id) in scholarship_info.get("delist_applicants")
    assert scholarship_info.get("delist_applicants_count") == 1
    assert scholarship_info.get("offered_applicants_count") == 0

    # Invalid college id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id=123&scholarship_id={scholarship_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id=123456789012345678901234"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Required college_id when de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Invalid application id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}"
        f"&scholarship_id={scholarship_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=["123"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Application id `123` must be a 12-byte input or a 24-character hex string"

    # Invalid scholarship id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}&scholarship_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Scholarship id `123` must be a 12-byte input or a 24-character hex string"

    # Wrong scholarship id for de-list applicants from scholarship.
    response = await http_client_test.post(
        f"/scholarship/delist_applicants/?college_id={college_id}"
        f"&scholarship_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Scholarship not found id: 123456789012345678901234"
