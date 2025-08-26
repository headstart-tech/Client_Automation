"""
This file contains test cases related to course routes
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_course_create_not_authorized(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/course/create/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_course_create_bad_credentials(http_client_test, setup_module):
    """
    Bad token for create course
    """
    response = await http_client_test.post(
        f"/course/create/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_course_create_field_required(
    http_client_test, college_super_admin_access_token, test_course_data, setup_module
):
    """
    Field required for create course
    """
    response = await http_client_test.post(
        f"/course/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_course_data,
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


# Todo - Need to fix following test case, currently it's failing
# @pytest.mark.asyncio
# async def test_course_create_no_permission(
#     http_client_test,
#     access_token,
#     test_course_data,
#     setup_module,
#     test_college_validation,
# ):
#     """
#     No permission for create course
#     """
#     response = await http_client_test.post(
#         f"/course/create/?college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {access_token}"},
#         json=test_course_data,
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_course_create(
        http_client_test,
        college_super_admin_access_token,
        test_course_data,
        setup_module,
        test_college_validation,
):
    """
    Create new course
    """
    test_course_data['course_name'] = "testing"
    response = await http_client_test.post(
        f"/course/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_course_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "New course created successfully."


@pytest.mark.asyncio
async def test_course_create_already_exist(
    http_client_test,
    college_super_admin_access_token,
    test_course_data,
    setup_module,
    test_college_validation,
):
    """
    Course already exist when try to create new course
    """
    test_course_data['course_name'] = "testing"
    response = await http_client_test.post(
        f"/course/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_course_data,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Course already exist."


@pytest.mark.asyncio
async def test_course_list_college_not_found(http_client_test, setup_module):
    """
    College not found for get course list
    """
    response = await http_client_test.get(f"/course/list/?feature_key={feature_key}")
    assert response.status_code == 422
    assert response.json()["detail"] == "College does not exist."


@pytest.mark.asyncio
async def test_course_list(http_client_test,
                           setup_module, test_course_validation):
    """
    Get course list of particular college
    """
    response = await http_client_test.get(
        f"/course/list/?college_id={str(test_course_validation.get('college_id'))}&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Courses data fetched successfully."


@pytest.mark.asyncio
async def test_course_list_by_course_names(http_client_test, setup_module, test_course_validation):
    """
    Get course list of particular college
    """
    response = await http_client_test.get(
        f"/course/list/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_name={test_course_validation.get('course_name')}&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Courses data fetched successfully."


@pytest.mark.asyncio
async def test_course_list_by_invalid_category(http_client_test, setup_module, test_course_validation):
    """
    Get course list of particular college by invalid category
    """
    response = await http_client_test.get(
        f"/course/list/?college_id={str(test_course_validation.get('college_id'))}&feature_key={feature_key}&category=")
    assert response.status_code == 400
    assert response.json()["detail"] == "Category must be required and valid."


@pytest.mark.asyncio
async def test_course_list_by_category(http_client_test, setup_module, test_health_science_course_validation):
    """
    Get course list of particular college by category
    """
    response = await http_client_test.get(
        f"/course/list/?college_id={str(test_health_science_course_validation.get('college_id'))}"
        f"&category=health_science&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Courses data fetched successfully."
    assert response.json()['data'] is not None
    assert response.json()['data'][0][0]['college_id'] == str(test_health_science_course_validation.get('college_id'))


@pytest.mark.asyncio
async def test_course_list_by_category_and_pagination(http_client_test, setup_module,
                                                      test_health_science_course_validation):
    """
    Get course list of particular college by category and pagination
    """
    response = await http_client_test.get(
        f"/course/list/?college_id={str(test_health_science_course_validation.get('college_id'))}"
        f"&category=health_science&page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Courses data fetched successfully."
    assert response.json()['data'] is not None
    assert response.json()['data'][0]['college_id'] == str(test_health_science_course_validation.get('college_id'))
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None


@pytest.mark.asyncio
async def test_course_list_college_not_found(http_client_test, setup_module):
    """
    Get course list of particular college
    """
    response = await http_client_test.get(
        f"/course/list/?college_id=123456789012345678901234&feature_key={feature_key}")
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."


@pytest.mark.asyncio
async def test_course_status_not_authorized(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(f"/course/status/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_course_status_bad_credentials(http_client_test, setup_module):
    """
    Bad token for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_course_status_field_required(
    http_client_test, college_super_admin_access_token, setup_module
):
    """
    Field required for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_course_status_body_field_required(
    http_client_test, access_token, setup_module, test_course_validation
):
    """
    Body field required for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_course_status_no_permission(
    http_client_test, access_token, setup_module, test_course_validation
):
    """
    No permission for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"is_activated": False},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_course_status(
    http_client_test, college_super_admin_access_token, setup_module
):
    """
    Update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id=628dfd41ef796e8f757a5c13"
        f"&course_id=628f39c0cb69fc0789e69183&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": True},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Unable to update, no changes have been made."}


@pytest.mark.asyncio
async def test_course_status(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_course_validation,
):
    """
    Update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": False},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Course status updated successfully."


@pytest.mark.asyncio
async def test_course_status_college_not_exist(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_course_validation,
):
    """
    College not exist for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id=123456789012345678901234&course_id={(test_course_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": True},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."


@pytest.mark.asyncio
async def test_course_status_course_not_exist(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_college_validation,
):
    """
    Course not exist for update course status
    """
    response = await http_client_test.put(
        f"/course/status/?college_id={str(test_college_validation.get('_id'))}"
        f"&course_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": True},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."


@pytest.mark.asyncio
async def test_edit_course_not_authorized(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(f"/course/edit/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_edit_course_bad_credentials(http_client_test, setup_module):
    """
    Bad token for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_edit_course_no_permission(
    http_client_test, access_token, test_college_validation, test_course_data, setup_module
):
    """
    No permission for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?college_id={str(test_college_validation.get('_id'))}"
        f"&course_id=625936da079c240edf9c7653&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"banner_image_url": "test.txt"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_edit_course_field_required(
    http_client_test, college_super_admin_access_token, setup_module
):
    """
    Field required for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_edit_course(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_course_validation,
):
    """
    Edit course successfully
    """
    response = await http_client_test.put(
        f"/course/edit/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"banner_image_url": "test.txt"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Course updated successfully."


@pytest.mark.asyncio
async def test_edit_course_not_processable(
    http_client_test,
    college_super_admin_access_token,
    test_course_validation,
    setup_module,
):
    """
    At least 1 field required for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?college_id={str(test_course_validation.get('college_id'))}"
        f"&course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Need to pass atleast 1 field to update course."


@pytest.mark.asyncio
async def test_edit_course_college_not_found(
    http_client_test,
    college_super_admin_access_token,
    test_course_validation,
    setup_module,
):
    """
    College not found for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?college_id=123456789012345678901234&"
        f"course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"banner_image_url": "test.txt"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."


@pytest.mark.asyncio
async def test_edit_course_course_not_found(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
    test_college_validation,
):
    """
    Course not found. for edit course
    """
    response = await http_client_test.put(
        f"/course/edit/?college_id={str(test_college_validation.get('_id'))}"
        f"&course_id=625d5d99e506c239b8762df7&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"banner_image_url": "test.txt"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not exist."
