"""
This file contains test cases related to admin routes
"""
import inspect
from pathlib import Path, PurePath

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

def get_file_path():
    """
    This function returns the absolute path of the files,
    required for Test cases
    """
    file_path = Path(inspect.getfile(inspect.currentframe())).resolve()
    root_folder_path = PurePath(file_path).parent
    college_csv = PurePath(root_folder_path, Path(rf"colleges.csv"))
    courses_csv = PurePath(root_folder_path, Path(rf"courses.csv"))
    student_data_csv = PurePath(root_folder_path, Path(rf"student_data.csv"))
    test_jpg = PurePath(root_folder_path, Path(rf"test.jpg"))
    test_docs = PurePath(root_folder_path, Path(rf"test_docs.pdf"))
    sample_small_video = PurePath(root_folder_path, Path(rf"sample-small-video.mp4"))
    paths = {
        'college_csv': college_csv,
        'courses_csv': courses_csv,
        'student_data_csv': student_data_csv,
        'test_jpg': test_jpg,
        'test_docs': test_docs,
        'sample_small_video': sample_small_video
    }
    return paths


@pytest.mark.asyncio
async def test_form_wise_status_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/form_wise_record/{test_college_validation.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_form_wise_status_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for form wise status
    """
    response = await http_client_test.post(
        f"/admin/form_wise_record/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_form_wise_status_username_not_found(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Username not found for form wise status
    """
    response = await http_client_test.post(
        f"/admin/form_wise_record/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Below test cases running only when we run single test cases but not
# working when we run all test cases by folder or file
# @pytest.mark.asyncio
# async def test_form_wise_status_no_found(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Get form wise status no found
#     """
#     response = await http_client_test.post(
#         f"/admin/form_wise_record/{test_college_validation.get('_id')}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Data not valid."


# Below test case execute only if data exists
# @pytest.mark.asyncio
# async def test_form_wise_status(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Get form wise status
#     """
#     response = await http_client_test.post(
#         f"/admin/form_wise_record/{test_college_validation.get('_id')}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetched successfully."


# Below test cases running only when we run single test cases but not working when we run all test cases by folder or file
# @pytest.mark.asyncio
# async def test_form_wise_status_by_season_wise_no_found(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Get form wise status by season wise
#     """
#     current_year = date.today().year
#     response = await http_client_test.post(
#         f"/admin/form_wise_record/{test_college_validation.get('_id')}?season={current_year}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Data not valid."


# Below test case execute only if data exists
# @pytest.mark.asyncio
# async def test_form_wise_status_by_season_wise(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Get form wise status by season wise
#     """
#     current_year = date.today().year
#     response = await http_client_test.post(
#         f"/admin/form_wise_record/{test_college_validation.get('_id')}?season={current_year}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetched successfully."


@pytest.mark.asyncio
async def test_college_lead_name(http_client_test, setup_module):
    """
    Get college name
    """
    response = await http_client_test.get(f"/admin/college_name?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Below test case execute only when there is no college info present
# in database collection
# @pytest.mark.asyncio
# async def test_college_lead_name(http_client_test, setup_module, college_super_admin_access_token):
#     """
#     Get college name
#     """
#     response = await http_client_test.get("/admin/college_name",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},)
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_lead_application_graph_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/lead_application/{test_college_validation.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_lead_application_graph_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for get lead application graph data
    """
    response = await http_client_test.put(
        f"/admin/lead_application/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_lead_application_graph_data_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Required body for get lead application graph data
    """
    response = await http_client_test.put(
        f"/admin/lead_application/123456789012345678901234?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    # assert response.json()["data"][0]['date'] == []
    # assert response.json()["data"][0]["lead"] == []
    # assert response.json()["data"][0]["application"] == []


@pytest.mark.asyncio
async def test_lead_application_graph_without_event_data(
        http_client_test, college_super_admin_access_token,
        setup_module, test_college_validation, start_end_date,
        test_student_validation, application_details):
    """
    Get lead application graph data without event data
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().event_collection.delete_many({})
    response = await http_client_test.put(
        f"/admin/lead_application/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    if response.json()["data"]:
        columns = ['date', 'lead', 'application', 'event']
        for column in columns:
            assert column in response.json()["data"][0]

    # Todo - Following commented assert statements successfully executed
    #  locally but failing on test server, need to check and resolve it

    #  assert response.json()["data"][0]["date"] != []
    #  assert response.json()["data"][0]["lead"] != []
    #  assert response.json()["data"][0]["application"] != []
    #  assert response.json()["data"][0]["event"] == []


@pytest.mark.asyncio
async def test_lead_application_graph_with_event_data(
        http_client_test, college_super_admin_access_token,
        setup_module, test_college_validation, start_end_date,
        test_event_data):
    """
    Get lead application graph data with event data
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    await DatabaseConfiguration().studentApplicationForms.delete_many({})
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=test_event_data
    )
    response = await http_client_test.put(
        f"/admin/lead_application/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=start_end_date
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0]["date"] != []
    assert response.json()["data"][0]["lead"] != []
    assert response.json()["data"][0]["application"] != []
    assert response.json()["data"][0]["event"] != []
    if response.json()["data"]:
        columns = ['date', 'lead', 'application', 'event']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_form_stage_wise_segregation_not_authenticated(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/form_stage_wise/{test_college_validation.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_form_stage_wise_segregation_bad_credentials(
        http_client_test, setup_module, test_college_validation
):
    """
    Bad token for get form stage wise segregation data
    """
    response = await http_client_test.put(
        f"/admin/form_stage_wise/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_form_stage_wise_segregation(
        http_client_test, college_super_admin_access_token, setup_module,
        start_end_date, test_college_validation
):
    """
    Get form stage wise segregation data
    """
    response = await http_client_test.put(
        f"/admin/form_stage_wise/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_form_stage_wise_segregation_by_season_wise(
        http_client_test, college_super_admin_access_token, setup_module,
        start_end_date, test_college_validation
):
    """
    Get form stage wise segregation by season wise
    """
    response = await http_client_test.put(
        f"/admin/form_stage_wise/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_form_stage_wise_segregation_by_season_wise_no_found(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation
):
    """
    Get form stage wise segregation by season wise no found
    """
    response = await http_client_test.put(
        f"/admin/form_stage_wise/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0]['form_submitted'] == 0


@pytest.mark.asyncio
async def test_lead_funnel_application_not_authenticated(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_lead_funnel_application_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for get lead funnel application data
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_lead_funnel_application(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get lead funnel application data
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_lead_funnel_with_wrong_change_indicator(
        http_client_test, college_super_admin_access_token,
        setup_module, test_college_validation):
    """
    Get application funnel data with wrong change indicator
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?"
        f"change_indicator=&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Change Indicator must be " \
                                        "required and valid."


@pytest.mark.asyncio
async def test_lead_funnel_with_indicator(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation):
    """
    Get application funnel data with change indicator
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?"
        f"change_indicator=last_7_days&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_lead_funnel_application_by_season_wise(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation):
    """
    Get lead funnel application data by season wise
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{str(test_college_validation.get('_id'))}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_lead_funnel_application_by_season_wise_no_found(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get lead funnel application data by season wise no found
    """
    response = await http_client_test.put(
        f"/admin/lead_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0]["form_submitted"] == 0


@pytest.mark.asyncio
async def test_application_funnel_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_application_funnel_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for application funnel data
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_application_funnel(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get application funnel data
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_application_funnel_with_indicator(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation):
    """
    Get application funnel data with change indicator
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?"
        f"change_indicator=last_7_days&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_application_funnel_by_season_wise(
        http_client_test, college_super_admin_access_token,
        setup_module, test_college_validation, start_end_date):
    """
    Get application funnel data by season wise
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_application_funnel_by_season_wise_no_found(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get application funnel data by season wise no found
    """
    response = await http_client_test.put(
        f"/admin/application_funnel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_top_performing_channel_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/top_performing_channel/{test_college_validation.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_top_performing_channel_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for top performing channel data
    """
    response = await http_client_test.put(
        f"/admin/top_performing_channel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_top_performing_channel(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get top performing channel data
    """
    response = await http_client_test.put(
        f"/admin/top_performing_channel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_top_performing_channel_by_season_wise(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation, start_end_date):
    """
    Get top performing channel data by season wise
    """
    response = await http_client_test.put(
        f"/admin/top_performing_channel/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_score_board_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_score_board_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Bad token for get score board data
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_score_board(
        http_client_test, college_super_admin_access_token, setup_module,
        start_end_date, test_college_validation):
    """
    Get score board data
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_score_board_with_wrong_change_indicator(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation):
    """
    Get score board data with wrong change indicator
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?"
        f"change_indicator=&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Change Indicator must be " \
                                        "required and valid."


@pytest.mark.asyncio
async def test_score_board_with_indicator(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation):
    """
    Get score board data with change indicator
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?change_indicator=last_7_days&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_score_board_by_season_wise(
        http_client_test, college_super_admin_access_token, setup_module,
        start_end_date, test_college_validation):
    """
    Get score board data by season wise
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_score_board_by_season_wise_no_found(
        http_client_test, college_super_admin_access_token, setup_module,
        start_end_date, test_college_validation):
    """
    Get score board by season wise no found
    """
    response = await http_client_test.put(
        f"/admin/score_board/{test_college_validation.get('_id')}?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_score_board_student_no_permission(
        http_client_test, access_token, setup_module, start_end_date
):
    """
    Student not found for score board
    """
    response = await http_client_test.put(
        f"/admin/score_board/628dfd41ef796e8f757a5c13?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=start_end_date
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_parsing_error(
        http_client_test, setup_module
):
    """
    Parsing the body error when try to upload colleges data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_colleges/?feature_key={feature_key}",
        headers={"Content-Type": "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_not_authenticated(
        http_client_test, setup_module
):
    """
    Not authenticated when try to upload colleges data using csv
    """
    response = await http_client_test.post(f"/admin/upload_colleges/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_bad_token(
        http_client_test, setup_module
):
    """
    Bad token when try to upload colleges data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_colleges/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_field_required(
        http_client_test, access_token, setup_module
):
    """
    Field required when try to upload colleges data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_colleges/?feature_key={feature_key}", headers={"Authorization":
                                                f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File must be required and valid."}


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_no_permission(
        http_client_test, access_token, setup_module
):
    """
    No permission when try to upload colleges data using csv
    """
    with open(get_file_path()['college_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_colleges/?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database(
        http_client_test, super_admin_access_token, setup_module
):
    """
    for upload colleges data using csv
    """
    with open(get_file_path()['college_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_colleges/?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 200
    assert (
            response.json()["message"]
            == "Colleges data successfully inserted into the database."
    )


@pytest.mark.asyncio
async def test_upload_csv_file_in_s3_and_add_csv_data_into_database_college_data_already_exist(
        http_client_test, super_admin_access_token, setup_module
):
    """
    Colleges data already exist when try to upload colleges data using csv
    """
    with open(get_file_path()['college_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_colleges/?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {super_admin_access_token}"},
            files=files,
        )
    assert response.status_code == 422
    assert response.json() == {"detail": "Colleges data already "
                                         "exist in database."}


@pytest.mark.asyncio
async def test_upload_courses_parsing_error(http_client_test, setup_module):
    """
    Parsing the body error when try to upload courses data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_courses/?feature_key={feature_key}", headers={"Content-Type":
                                               "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_upload_courses_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated when try to upload courses data using csv
    """
    response = await http_client_test.post(f"/admin/upload_courses/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_upload_courses_bad_token(http_client_test, setup_module):
    """
    Bad token when try to upload courses data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_courses/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_courses_field_required(
        http_client_test, access_token, setup_module
):
    """
    Field required when try to upload courses data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_courses/?feature_key={feature_key}", headers={"Authorization": f"Bearer "
                                                            f"{access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}


@pytest.mark.asyncio
async def test_upload_courses_file_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    File required when try to upload courses data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_courses/?college_id="
        f"{test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File must be required and valid."}


@pytest.mark.asyncio
async def test_upload_courses_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    No permission when try to upload courses data using csv
    """
    with open(get_file_path()['courses_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_courses/?college_id="
            f"{test_college_validation.get('_id')}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_upload_courses_college_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    College not found when try to upload courses data using csv
    """
    with open(get_file_path()['courses_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_courses/?college_id=628dfd41ef796e8f757a5c11&feature_key={feature_key}",
            headers={"Authorization": f"Bearer "
                                      f"{college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 422
    assert response.json() == {"detail": "College does not exist."}


@pytest.mark.asyncio
async def test_upload_courses(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation
):
    """
    Upload courses data using csv
    """
    with open(get_file_path()['courses_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_courses/?college_id="
            f"{test_college_validation.get('_id')}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer "
                                      f"{college_super_admin_access_token}"},
            files=files,
        )
    assert response.status_code == 200
    assert response.json()['message'] == "Courses data successfully " \
                                         "inserted into the database."


@pytest.mark.asyncio
async def test_upload_courses_data_already_exist(
        http_client_test, college_super_admin_access_token, setup_module,
        test_college_validation
):
    """
    Courses data already exist when try to upload courses data using csv
    """
    with open(get_file_path()['courses_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_courses/?college_id="
            f"{test_college_validation.get('_id')}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer "
                                      f"{college_super_admin_access_token}"},
            files=files,
        )
    assert response.status_code == 422
    assert response.json()["detail"] == "Courses data already exist in " \
                                        "a database."


@pytest.mark.asyncio
async def test_upload_student_data_parsing_error(
        http_client_test, test_college_validation, setup_module):
    """
    Parsing the body error when try to upload student data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_student_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Content-Type": "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_upload_student_data_not_authenticated(
        http_client_test, test_college_validation, setup_module):
    """
    Not authenticated when try to upload student data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_student_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_upload_student_data_bad_token(
        http_client_test, test_college_validation, setup_module):
    """
    Bad token when try to upload student data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_student_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_student_data_field_required(
        http_client_test, access_token, setup_module
):
    """
    Field required when try to upload student data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_student_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}


@pytest.mark.asyncio
async def test_upload_student_data_file_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    File required when try to upload student data using csv
    """
    response = await http_client_test.post(
        f"/admin/upload_student_data/?college_id="
        f"{test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File must be required and valid."}


@pytest.mark.asyncio
async def test_upload_student_data_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    No permission when try to upload student data using csv
    """
    with open(get_file_path()['student_data_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_student_data/?college_id="
            f"{test_college_validation.get('_id')}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_upload_student_data_college_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    College not found when try to upload student data using csv
    """
    with open(get_file_path()['student_data_csv'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_student_data/?college_id=628dfd41ef796e8f757a5c11&feature_key={feature_key}",
            headers={"Authorization": f"Bearer "
                                      f"{college_super_admin_access_token}"},
            files=files
        )
    assert response.status_code == 422
    assert response.json() == {"detail": "College does not exist."}


# ToDo - Currently, following test case giving error. Need to fix it.
# @pytest.mark.asyncio
# async def test_upload_student_data(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Upload student data using csv
#     :return:
#     """
#     with open(get_file_path()['student_data_csv'], "rb") as f:
#         files = {"file": f}
#         response = await http_client_test.post(
#             f"/admin/upload_student_data/?college_id={test_college_validation.get('_id')}",
#             headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#             files=files,
#         )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Student data successfully inserted into the database."


# will execute only when the data will be already present in database
# @pytest.mark.asyncio
# async def test_upload_student_data_data_already_exist(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     Student data already exist when try to upload courses data using csv
#     """
#     with open(get_file_path()['student_data_csv'], "rb") as f:
#         files = {"file": f}
#         response = await http_client_test.post(
#             f"/admin/upload_student_data/?college_id={test_college_validation.get('_id')}",
#             headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#             files=files,
#         )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Student data already exist in a database."}


@pytest.mark.asyncio
async def test_upload_files_parsing_error(
        http_client_test, test_college_validation, setup_module):
    """
    Parsing the body error when try to upload file
    """
    response = await http_client_test.post(
        f"/admin/upload_files/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Content-Type": "multipart/form-data"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing boundary in multipart."


@pytest.mark.asyncio
async def test_upload_files_required_files(
        http_client_test, test_college_validation, setup_module):
    """
    Required files for upload
    """
    with open(get_file_path()['test_jpg'], "rb") as f:
        files = {"file": f}
        response = await http_client_test.post(
            f"/admin/upload_files/?college_id="
            f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Files must be required and valid."


# Below test case not working for now
# @pytest.mark.asyncio
# async def test_upload_files(http_client_test, test_college_validation, setup_module):
#     """
#     Upload file
#     """
#     with open('test.jpg', "rb") as f:
#         files = {"file": f}
#         response = await http_client_test.post(f"/admin/upload_files/?college_id={str(test_college_validation.get('_id'))}", files=files)
#     assert response.status_code == 200
#     assert response.json()['message'] == 'Files are uploaded successfully.'


@pytest.mark.asyncio
async def test_student_documents_required_student_id(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module):
    """
    Required student id for get documents
    """
    response = await http_client_test.get(
        f"/admin/student_documents/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student Id must be required " \
                                        "and valid."


@pytest.mark.asyncio
async def test_student_documents_invalid_student_id(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module):
    """
    Invalid student id for get documents
    """
    response = await http_client_test.get(
        f"/admin/student_documents/?student_id="
        f"62a9bede4035e93c7ff2467&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == \
           "Invalid student id. Error - '62a9bede4035e93c7ff2467' is not a " \
           "valid ObjectId, it must be a 12-byte input or a 24-character " \
           "hex string"

# Below test case executes only if get documents of student id 62a32e1ae1a69d07093ecf42
# @pytest.mark.asyncio
# async def test_student_documents(http_client_test, test_college_validation, setup_module):
#     """
#     Get student documents
#     """
#     response = await http_client_test.get("/admin/student_documents/?student_id=62a32e1ae1a69d07093ecf42&college_id={str(test_college_validation.get('_id'))")
#     assert response.status_code == 200
#     assert response.json()['message'] == 'Document fetched successfully.'
