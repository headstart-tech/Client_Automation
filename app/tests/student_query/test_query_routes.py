"""
This file contains test cases regarding query routes
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo - We will cover all possible test cases for query routes and
#  separate queries test cases based on API routes.
@pytest.mark.asyncio
async def test_query_list_not_found(http_client_test, test_college_validation, setup_module, college_super_admin_access_token):
    """
    Queries not found for get query list
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queries.delete_many({})
    response = await http_client_test.post(
        f"/query/list/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
           headers={
               "Authorization": f"Bearer {college_super_admin_access_token}"},
           )
    assert response.status_code == 200
    assert response.json()["message"] == "Queries not found."
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_student_query_not_authorized(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/student_query/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_student_query_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_student_query_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required to add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Title must be required and valid."


@pytest.mark.asyncio
async def test_student_query_no_permission(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    No permission for successfully add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_student_query_category_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Category required for add student query
    """
    response = await http_client_test.post(
        "/student_query/create/?title=test&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Category Name must be required and valid."}


@pytest.mark.asyncio
async def test_student_query_required_course_name(
        http_client_test, test_college_validation, access_token, setup_module,
        create_query_categories
):
    """
    Required course name for add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?title=test&category_name=General%20Query&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail":
                                   "Course Name must be required and valid."}


@pytest.mark.asyncio
async def test_student_query_invalid_category_name(
        http_client_test, test_college_validation, access_token, setup_module,
        test_course_validation
):
    """
    Invalid category name for add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?title=test&category_name=test&"
        f"college_id={str(test_college_validation.get('_id'))}"
        f"&course_name={test_course_validation.get('course_name')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Category name should be any of the following: "
                  "General Query, Payment Related Query, Application "
                  "Query and Other Query."
    }


@pytest.mark.asyncio
async def test_student_query(
        http_client_test, test_college_validation, access_token, setup_module,
        create_query_categories, test_course_validation
):
    """
    Invalid category name for add student query
    """
    response = await http_client_test.post(
        f"/student_query/create/?title=test&category_name=General%20Query&"
        f"college_id={str(test_college_validation.get('_id'))}"
        f"&course_name={test_course_validation.get('course_name')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Query added."


@pytest.mark.asyncio
async def test_query_list(http_client_test, test_college_validation,
                          setup_module, query_details, college_super_admin_access_token):
    """
    Get query list
    """
    response = await http_client_test.post(
        f"/query/list/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get queries list successfully."


@pytest.mark.asyncio
async def test_query_reply_not_authorized(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/query/reply/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_query_reply_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for reply to query
    """
    response = await http_client_test.post(
        f"/query/reply/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_query_reply_body_required(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Body required for reply to query
    """
    response = await http_client_test.post(
        f"/query/reply/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."


@pytest.mark.asyncio
async def test_query_reply_required_field(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Field required for reply to query
    """
    response = await http_client_test.post(
        f"/query/reply/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"reply": "Sorry for inconvenience cause to you."},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Need to pass query id or ticket id"


@pytest.mark.asyncio
async def test_query_reply(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, query_details
):
    """
    Field required to add student query
    """
    response = await http_client_test.post(
        f"/query/reply/?query_id={str(query_details['_id'])}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"reply": "Sorry for inconvenience cause to you."},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Reply sent."


@pytest.mark.asyncio
async def test_query_reply_invalid_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Field required to add student query
    """
    response = await http_client_test.post(
        f"/query/reply/?query_id=230f2d004f2ac48a57858c"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"reply": "Sorry for inconvenience cause to you."},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Query id must be a 12-byte input or a 24-character hex string."
    )


@pytest.mark.asyncio
async def test_change_status_of_query_not_authorized(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/query/change_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_change_status_of_query_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for change status of query
    """
    response = await http_client_test.put(
        f"/query/change_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_change_status_of_query_ticket_id_required(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Ticket id required for change status to query
    """
    response = await http_client_test.put(
        f"/query/change_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Ticket Id must be required and valid."


@pytest.mark.asyncio
async def test_change_status_of_query_required_status(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, query_details
):
    """
    Status required for change status of query
    """
    response = await http_client_test.put(
        f"/query/change_status/?ticket_id={str(query_details['ticket_id'])}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Status must be required and valid."


@pytest.mark.asyncio
async def test_change_status_of_query_not_found(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module
):
    """
    Query not found for change status of query
    """
    response = await http_client_test.put(
        f"/query/change_status/?ticket_id=22-08-317&status=IN%20PROGRESS&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Query not found."


@pytest.mark.asyncio
async def test_change_status_of_query_invalid_status(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, query_details
):
    """
    Invalid status for change status of query
    """
    response = await http_client_test.put(
        f"/query/change_status/?ticket_id={str(query_details['ticket_id'])}"
        f"&status=IN%20PROGRES&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Status should be any of the following: TO DO, IN PROGRESS and DONE."
    )


@pytest.mark.asyncio
async def test_change_status_of_query(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, query_details
):
    """
    Change status of query
    """
    response = await http_client_test.put(
        f"/query/change_status/?ticket_id={query_details.get('ticket_id')}"
        f"&status=DONE&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Query status changed."


@pytest.mark.asyncio
async def test_get_query_details_not_authorized(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/query/get/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_query_details_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get query details
    """
    response = await http_client_test.get(
        f"/query/get/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_query_details_required_field(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required field for get query details
    """
    response = await http_client_test.get(
        f"/query/get/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Need to pass application id or ticket id."


@pytest.mark.asyncio
async def test_get_query_details_by_invalid_ticket_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid ticket id for get query details
    """
    response = await http_client_test.get(
        f"/query/get/?ticket_id=22-08-3&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Query not found."


@pytest.mark.asyncio
async def test_get_query_details_by_invalid_application_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid application id for get query details
    """
    response = await http_client_test.get(
        f"/query/get/?application_id=23cab0bca14aba087d2930"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Application id must be a 12-byte input or a 24-character hex string."
    )


@pytest.mark.asyncio
async def test_get_query_details_by_application_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        application_details,
):
    """
    Get query details by application id
    """
    response = await http_client_test.get(
        f"/query/get/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all student queries."


@pytest.mark.asyncio
async def test_get_query_details_by_ticket_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, query_details
):
    """
    Get query details
    """
    response = await http_client_test.get(
        f"/query/get/?ticket_id={str(query_details['ticket_id'])}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get query details of ticket id."


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_not_authorized(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_required_college_id(
    http_client_test, college_super_admin_access_token, setup_module
):
    """
    Required college id for assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "College Id must be required and valid."


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_required_ticket_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module
):
    """
    Required ticket id for assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Ticket Id must be required and valid."


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_required_counselor_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        query_details,
):
    """
    Required counselor id for assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&ticket_id={query_details.get('ticket_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Enter counselor id or user_name."


@pytest.mark.asyncio
async def test_assigned_query_to_counselor_invalid_ticket_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_counselor_validation,
):
    """
    Invalid ticket id for assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&ticket_id=22-08-3&counselor_id={str(test_counselor_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Query not found."


@pytest.mark.asyncio
async def test_assigned_query_to_counselor(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        query_details,
        test_counselor_validation,
):
    """
    Assign query to counselor
    """
    response = await http_client_test.put(
        f"/query/assigned_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&ticket_id={query_details.get('ticket_id')}&counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
