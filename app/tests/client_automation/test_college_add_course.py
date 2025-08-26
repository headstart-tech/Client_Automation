import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_course_not_authenticated(http_client_test, client_automation_test_course_data, test_college_validation):
    """Test adding a course without authentication."""
    response = await http_client_test.post(
        f"/client_automation/{str(test_college_validation.get('_id'))}/add_course?feature_key={feature_key}",
        json=client_automation_test_course_data
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_add_course_invalid_token(http_client_test, client_automation_test_course_data, test_college_validation):
    """Test adding a course with an invalid token."""
    response = await http_client_test.post(
        f"/client_automation/{str(test_college_validation.get('_id'))}/add_course?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong"},
        json=client_automation_test_course_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_add_course_invalid_college_id(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_college_validation):
    """Test adding a course with an invalid college ID."""
    response = await http_client_test.post(
        f"/client_automation/123/add_course?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=client_automation_test_course_data
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'College id must be a 12-byte input or a 24-character hex string'}

@pytest.mark.asyncio
async def test_add_course_college_not_found(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_college_validation):
    """Test adding a course when the college is not found."""
    response = await http_client_test.post(
        f"/client_automation/60f1b9b3e4b3b3b3b3b3b3b3/add_course?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=client_automation_test_course_data
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'College not found.'}


# @pytest.mark.asyncio
# async def test_add_course_success(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_college_validation):
#     """Test successfully adding a course."""
#     from app.database.configuration import DatabaseConfiguration
#     query = {"status": {"$in": ["pending", "partially_approved"]}}
#     pending_approvals = await DatabaseConfiguration().approvals_collection.find(query).to_list(length=None)
#     for approvals in pending_approvals:
#         await http_client_test.put(
#             f"/approval/update_status/{str(approvals['_id'])}?feature_key={feature_key}",
#             headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#             params={"status": "reject"},
#             json={"remarks": "Not good"}
#         )
#     await DatabaseConfiguration().course_collection.delete_one({"course_name": client_automation_test_course_data.get("course_lists")[0].get("course_name")})
#     response = await http_client_test.post(
#         f"/client_automation/{str(test_college_validation.get('_id'))}/add_course?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=client_automation_test_course_data
#     )
#     assert response.status_code == 200
#     approval_id = response.json().get("approval_id")
#
#     response = await http_client_test.put(
#         f"/approval/update_status/{approval_id}?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         params={"status": "approve"},
#         json={"remarks": "Looks good"}
#     )
#     assert response.status_code == 200
#     response = await http_client_test.put(
#         f"/approval/update_status/{approval_id}?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         params={"status": "approve"},
#         json={"remarks": "Looks good"}
#     )
#     assert response.status_code == 200
#
# @pytest.mark.asyncio
# async def test_add_course_already_exists(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_college_validation):
#     """Test adding a course that already exists."""
#     response = await http_client_test.post(
#         f"/client_automation/{str(test_college_validation.get('_id'))}/add_course?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=client_automation_test_course_data
#     )
#     assert response.status_code == 422

@pytest.mark.asyncio
async def test_add_course_repeated_school_ignore(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_client_automation_college_id):
    """Test adding a course details where school that already exists."""
    client_automation_test_course_data.pop("course_lists")
    client_automation_test_course_data.pop("preference_details")
    response = await http_client_test.post(
        f"/client_automation/{str(test_client_automation_college_id)}/add_course?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=client_automation_test_course_data
    )
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "reject"},
        json={"remarks": "Not good"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_course_preference_insufficient_fields(http_client_test, college_super_admin_access_token, client_automation_test_course_data, test_college_validation):
    """Test adding preference details that have insufficient fields."""
    client_automation_test_course_data.pop("course_lists")
    client_automation_test_course_data.pop("school_names")
    client_automation_test_course_data["preference_details"].pop("fees_of_trigger")
    response = await http_client_test.post(
        f"/client_automation/{str(test_college_validation.get('_id'))}/add_course?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=client_automation_test_course_data
    )
    assert response.status_code == 422