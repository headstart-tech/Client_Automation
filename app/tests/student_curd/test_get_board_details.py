"""
This file contains test cases for get board details
"""
import pytest


@pytest.mark.asyncio
async def test_get_board_details(http_client_test, setup_module, test_college_validation):
    """
    Get board details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().boardDetails.insert_one(
        {"tenth_board_name": ["AKTU"], "inter_board_name": ["ANDHRA PRADESH BOARD OF INTERMEDIATE EDUCATION"]})
    response = await http_client_test.get(
        f"/student_user_crud/board_detail/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json()['message'] == "data fetch successfully."


@pytest.mark.asyncio
async def test_get_board_details_not_found(http_client_test, setup_module, test_college_validation):
    """
    Not found for get board details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().boardDetails.delete_many({})
    response = await http_client_test.get(
        f"/student_user_crud/board_detail/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 404
    assert response.json()['detail'] == "Board not found."


@pytest.mark.asyncio
async def test_get_board_details_required_college_id(http_client_test, setup_module, test_college_validation):
    """
    Required college id for get board details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().boardDetails.delete_many({})
    response = await http_client_test.get(f"/student_user_crud/board_detail/")
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and valid."
