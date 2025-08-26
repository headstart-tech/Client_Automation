"""
This file contains test cases of marking details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_marking_details_not_authenticated(http_client_test, test_college_validation, setup_module, access_token,
                                                 college_super_admin_access_token, test_user_validation, test_marking_details_by_programname):
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
        f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_marking_details_bad_token(http_client_test, test_college_validation, setup_module, access_token,
                                    college_super_admin_access_token, test_user_validation, test_marking_details_by_programname
                                    ):
    # Bad token to get details
    response = await http_client_test.get(
         f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
         f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}&college_id="
         f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_marking_details_required_course_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_marking_details_by_programname
                                             ):
    # Required course name
    response = await http_client_test.get(
         f"/interview/marking_details/?specialization_name="
         f"{test_marking_details_by_programname.get('specialization_name')}&college_id="
         f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Course Name must be required and valid.'


@pytest.mark.asyncio
async def test_marking_details_required_spec_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation,test_marking_details_by_programname
                                             ):
    # Required spec name
    response = await http_client_test.get(
         f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
         f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Specialization Name must be required and valid.'



@pytest.mark.asyncio
async def test_get_marking_details_required_college_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation,test_marking_details_by_programname
                                             ):
    # Required college id
    response = await http_client_test.get(
         f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
         f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}"
         f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'



@pytest.mark.asyncio
async def test_marking_details_invalid_college_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation,test_marking_details_by_programname
                                             ):
    # Invalid college id
    response = await http_client_test.get(
         f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
         f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}&college_id=123456"
         f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_marking_details_college_not_found(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_marking_details_by_programname
                                             ):
    # College not found
    response = await http_client_test.get(
         f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
         f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}&"
         f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_marking_details(http_client_test, test_college_validation, setup_module, access_token,
                               college_super_admin_access_token, test_user_validation
                               , test_marking_details_by_programname):
    #get marking details
    response = await http_client_test.get(
        f"/interview/marking_details/?course_name={test_marking_details_by_programname.get('course_name')}"
        f"&specialization_name={test_marking_details_by_programname.get('specialization_name')}&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "gd" in response.json()



