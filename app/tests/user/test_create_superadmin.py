"""
This file contains test cases of create superadmin
"""
import pytest

# commented below test case because it will give error if super_admin already exist in database
# @pytest.mark.asyncio
# async def test_create_super_admin(http_client_test):
#     """
#     Test case -> for create SuperAdmin successfully
#     :param http_client_test:
#     :return:
#     """
#     response = await http_client_test.post("/user/create_super_admin/")
#     assert response.status_code == 200
#     assert response.json()['message'] == "SuperAdmin created successfully."


@pytest.mark.asyncio
async def test_create_super_admin_already_exist(http_client_test, setup_module):
    """
    Test case -> if super admin already exist
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post("/user/create_super_admin/")
    assert response.status_code == 422
    assert response.json()["detail"] == "SuperAdmin already exist."
