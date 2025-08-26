"""
This file contains testcases related to master stage Creation
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_master_stage(http_client_test, setup_module,
                                        college_super_admin_access_token, access_token,
                                        test_college_validation, test_super_admin_validation,
                                  ):
    """
    Different test cases to test master stage creation.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - access_token: A fixture which create student if not exist
            and return access token for student.
        - test_student_validation: A fixture which create student if not exist and return student data.
        - test_college_validation: A fixture which create college if not exist and return college data.
        - test_super_admin_validation: A fixture which create super admin if not exist and return access token of super admin.
    Assertions:
        response status code and json message.
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/master_stages/create_master_stage?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create Master Stages
    response = await http_client_test.post(
        f"/master_stages/create_master_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful stage creation
    valid_stage_data = {
        "stage_name": "Sample Stage",
        "stage_order": 1,
        "sub_stages": []
    }
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().stages.delete_many({})
    response = await http_client_test.post(
        f"/master_stages/create_master_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_stage_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Stage created successfully"

    # Duplicate stage name
    response = await http_client_test.post(
        f"/master_stages/create_master_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_stage_data,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Stage name already exists"

    # Missing required fields
    invalid_stage_data = {"stage_order": 2}
    response = await http_client_test.post(
        f"/master_stages/create_master_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=invalid_stage_data,
    )
    assert response.status_code == 400

    # Invalid sub_stage structure
    invalid_stage_data = {
        "stage_name": "Invalid Stage",
        "stage_order": 3,
        "sub_stages": [{"sub_stage_id": "invalid_id", "sub_stage_order": 1}]
    }



