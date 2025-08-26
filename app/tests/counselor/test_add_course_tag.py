"""
This file contain test cases for assign course to counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_course_tag_not_authenticated(
        http_client_test, test_counselor_validation, test_course_validation,
        setup_module):
    """
    Not authenticate for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course"
        f"?counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&course_name={str(test_course_validation.get('course_name'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_add_course_tag_required_college_id(http_client_test,
                                                  access_token,
                                                  test_course_validation,
                                                  test_counselor_validation,
                                                  setup_module):
    """
    No permission for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course"
        f"?counselor_id={str(test_counselor_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": []})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_add_course_tag_not_permission(http_client_test,
                                             test_college_validation,
                                             access_token,
                                             test_course_validation,
                                             test_counselor_validation,
                                             setup_module):
    """
    No permission for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course"
        f"?counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": ["HR"],
              "source_name": []})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_course_tag_counselor_id(http_client_test,
                                           test_college_validation,
                                           college_super_admin_access_token,
                                           setup_module,
                                           test_course_validation,
                                           test_counselor_validation):
    """
    Assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course"
        f"?counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}"
        f"&course_name={str(test_course_validation.get('course_name'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": ["HR"],
              "source_name": []})
    assert response.status_code == 200
    assert response.json()["message"] == "counselor assign successfully"


@pytest.mark.asyncio
async def test_add_course_tag_wrong_counselor_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        test_course_validation,
        setup_module):
    """
    Wrong counselor_id for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course?counselor_id=1234567890123456789012"
        f"&course_name={str(test_course_validation.get('course_name'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": ["HR"],
              "source_name": []})
    assert response.status_code == 404
    assert response.json()["detail"] == "counselor not found"


@pytest.mark.asyncio
async def test_add_course_tag_invalid_course_name(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_counselor_validation):
    """
    Invalid course_name for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course"
        f"?counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}"
        f"&course_name=b.sc&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": ["wrong_name"],
              "state_code": ["HR"],
              "source_name": []})
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found"


@pytest.mark.asyncio
async def test_add_course_tag_invalid_counselor_permission(
        http_client_test,
        test_college_validation,
        college_counselor_access_token,
        setup_module,
        test_course_validation,
        test_counselor_validation):
    """
    Invalid counselor_id for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course?counselor_id=123456789012345678901234"
        f"&course_name={str(test_course_validation.get('course_name'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": ["HR"],
              "source_name": []})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_add_course_tag_invalid_state_code(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_course_validation,
        test_counselor_validation):
    """
    Invalid state_code for assign course to counselor
    """
    response = await http_client_test.post(
        f"/counselor/assign_course?counselor_id=123456789012345678901234"
        f"&course_name={str(test_course_validation.get('course_name'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": [test_course_validation.get('course_name')],
              "state_code": ["HB"],
              "source_name": []})
    assert response.status_code == 404
    assert response.json()["detail"] == "State not found"
