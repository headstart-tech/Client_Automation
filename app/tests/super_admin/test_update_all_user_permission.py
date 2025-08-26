"""
This file contains test cases for update menu and permissions for different user types.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_users_menu_and_permission(
    http_client_test, setup_module, super_admin_access_token, access_token
):
    """
    Different test cases of update menu and permission for users.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        super_admin_access_token: A fixture which create super admin if not exist
            and return access token of super admin.
        access_token: A fixture which create student if not exist
            and return access token of student.

    Assertions:\n
        response status code and json message.
    """
    # Test case -> not authenticated if user not logged in
    response = await http_client_test.put("/super_admin/update_users_menu_permission/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Test case -> bad token for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Test case -> User Types required for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # Test case -> for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=[{"user_type": "super_admin",
               "menus": {"dashboard": {"admin_dashboard": {"menu": True}}}}]
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Updated menu permission."

    # Test case -> wrong role name for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=[{"user_type": "test", "menus": [{"dashboard": {"admin_dashboard": {"menu": True}}}]}]
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Role `test` not found"

    # Test case -> for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=[{"user_type": "super_admin"}]
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Menu permission not updated for Role `super_admin`."}

    # Test case -> no permission for update menu and permissions of users
    response = await http_client_test.put(
        f"/super_admin/update_users_menu_permission/?user_type=super_admin&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
