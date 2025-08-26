""" This File Contains Test Cases for Creating Admin User """
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# ========================================================================
# Test Cases for Create Admin User
# =======================================================================


# Exception for this Test Case
# : Get All Admins Not Found (Empty Collection)
@pytest.mark.asyncio
async def test_get_all_admins_not_found(setup_module, http_client_test, college_super_admin_access_token):
    """ Test Case: Get All Admins Not Found When No Admins Exist """
    # clear_admin_collection fixture should remove all admin docs
    response = await http_client_test.get(
        f"/admin/get_all_admins?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404


# Test Case: Create Admin User Without Authentication
@pytest.mark.asyncio
async def test_create_admin_unauthenticated(setup_module, http_client_test, test_new_admin_data):
    """ Test Case: Create Admin User Without Authentication """
    response = await http_client_test.post(f"/admin/create?feature_key={feature_key}", json=test_new_admin_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Create Admin User With Invalid Token
@pytest.mark.asyncio
async def test_create_admin_invalid_token(setup_module, http_client_test, test_new_admin_data):
    """ Test Case: Create Admin User With Invalid Token """
    response = await http_client_test.post(
        f"/admin/create?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json=test_new_admin_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Create Admin User When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_create_admin_permission_denied(setup_module, http_client_test, access_token, test_new_admin_data):
    """ Test Case: Create Admin User When User Has Insufficient Permissions """
    response = await http_client_test.post(
        f"/admin/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_new_admin_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Successfully Create Admin User
@pytest.mark.asyncio
async def test_create_admin_success(setup_module, http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Successfully Create Admin User """
    from app.database.configuration import DatabaseConfiguration
    DatabaseConfiguration().user_collection.delete_many({
        "user_type": "admin", "email": test_new_admin_data.get("email")
    })
    response = await http_client_test.post(
        f"/admin/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_new_admin_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Admin Created Successfully"
    assert "admin_id" in data

    # Optionally verify that the admin user exists in the database
    admin_id = data.get("admin_id")
    created_admin = await DatabaseConfiguration().user_collection.find_one(
        {"_id": ObjectId(admin_id), "user_type": "admin"}
    )
    assert created_admin is not None


# Test Case: Create Admin User With Duplicate Email or Mobile Number
@pytest.mark.asyncio
async def test_create_admin_duplicate_email_mobile(setup_module, http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Create Admin User With Duplicate Email or Mobile Number """
    response = await http_client_test.post(
        f"/admin/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_new_admin_data
    )
    assert response.status_code == 422
    assert "already exists" in response.json().get("detail", "")


# ========================================================================
# Test Cases for Get Admin User by Id
# =======================================================================


# Test Case: Get Admin By Id Without Authentication
@pytest.mark.asyncio
async def test_get_admin_by_id_unauthenticated(http_client_test):
    """ Test Case: Get Admin By Id Without Authentication """
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        params={"admin_id": "123456789012345678901234"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Get Admin By Id With Invalid Token
@pytest.mark.asyncio
async def test_get_admin_by_id_invalid_token(http_client_test):
    """ Test Case: Get Admin By Id With Invalid Token """
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        params={"admin_id": "123456789012345678901234"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Get Admin By Id When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_get_admin_by_id_permission_denied(http_client_test, access_token):
    """ Test Case: Get Admin By Id When User Has Insufficient Permissions """
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"admin_id": "123456789012345678901234"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Get Admin By Id With Invalid Id Format
@pytest.mark.asyncio
async def test_get_admin_by_id_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Get Admin By Id With Invalid Id Format """
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"admin_id": "invalid_id"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin id"}


# Test Case: Get Admin By Id Not Found
@pytest.mark.asyncio
async def test_get_admin_by_id_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Get Admin By Id Not Found """
    fake_id = ObjectId()
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"admin_id": str(fake_id)}
    )
    assert response.status_code == 404



# Test Case: Super Admin Retrieves Any Admin Successfully
@pytest.mark.asyncio
async def test_get_admin_by_id_super_admin(http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Super Admin Retrieves Any Admin Successfully """
    from app.database.configuration import DatabaseConfiguration
    admin = await DatabaseConfiguration().user_collection.find_one({
        "user_type": "admin", "email": test_new_admin_data.get("email")
    })
    admin_id = str(admin.get("_id"))
    response = await http_client_test.get(
        f"/admin/get_admin_by_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"admin_id": admin_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == admin_id
    assert data["email"] == admin["email"]
    # Ensure password is omitted
    assert "password" not in data


#########################################################################
# Test Cases for Get All Admin Users
########################################################################


# Test Case: Get All Admins Without Authentication
@pytest.mark.asyncio
async def test_get_all_admins_unauthenticated(http_client_test):
    """ Test Case: Get All Admins Without Authentication """
    response = await http_client_test.get(f"/admin/get_all_admins?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Get All Admins With Invalid Token
@pytest.mark.asyncio
async def test_get_all_admins_invalid_token(http_client_test):
    """ Test Case: Get All Admins With Invalid Token """
    response = await http_client_test.get(
        f"/admin/get_all_admins?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Get All Admins When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_get_all_admins_permission_denied(http_client_test, access_token):
    """ Test Case: Get All Admins When User Has Insufficient Permissions """
    response = await http_client_test.get(
        f"/admin/get_all_admins?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Successfully Get All Admins (No Pagination)
@pytest.mark.asyncio
async def test_get_all_admins_success_no_pagination(http_client_test, college_super_admin_access_token):
    """ Test Case: Successfully Get All Admins Without Pagination """
    # test_admins fixture inserts multiple admin docs
    response = await http_client_test.get(
        f"/admin/get_all_admins?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Admin Data List Found"
    assert isinstance(data.get("admins"), list)
    # Ensure passwords are omitted
    for admin in data["admins"]:
        assert "password" not in admin


# Test Case: Successfully Get All Admins With Pagination
@pytest.mark.asyncio
async def test_get_all_admins_success_with_pagination(http_client_test, super_admin_token):
    """ Test Case: Successfully Get All Admins With Pagination """
    # Assuming test_admins has at least 2 items
    response = await http_client_test.get(
        f"/admin/get_all_admins?page=1&limit=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert response.status_code == 200


#########################################################################
# Test Cases for Update Admin
########################################################################

# Test Case: Update Admin Details Without Authentication
@pytest.mark.asyncio
async def test_update_admin_unauthenticated(http_client_test):
    """ Test Case: Update Admin Details Without Authentication """
    response = await http_client_test.put(
        f"/admin/update_admin?feature_key={feature_key}",
        params={"admin_id": "123456789012345678901234"},
        json={"first_name": "NewName"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Update Admin Details With Invalid Token
@pytest.mark.asyncio
async def test_update_admin_invalid_token(http_client_test):
    """ Test Case: Update Admin Details With Invalid Token """
    response = await http_client_test.put(
        f"/admin/update_admin?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        params={"admin_id": "123456789012345678901234"},
        json={"first_name": "NewName"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Update Admin Details When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_update_admin_permission_denied(http_client_test, access_token):
    """ Test Case: Update Admin Details When User Has Insufficient Permissions """
    response = await http_client_test.put(
        f"/admin/update_admin?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"admin_id": "123456789012345678901234"},
        json={"first_name": "NewName"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Update Admin Details With Invalid Id Format
@pytest.mark.asyncio
async def test_update_admin_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Update Admin Details With Invalid Id Format """
    response = await http_client_test.put(
        f"/admin/update_admin?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"admin_id": "invalid_id"},
        json={"first_name": "NewName"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin id"}


# Test Case: Update Admin Details Not Found
@pytest.mark.asyncio
async def test_update_admin_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Update Admin Details Not Found """
    fake_id = ObjectId()
    response = await http_client_test.put(
        f"/admin/update_admin?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"admin_id": str(fake_id)},
        json={"first_name": "NewName"}
    )
    assert response.status_code == 404


# # Test Case: Updates Admin's Email and Mobile Successfully
# @pytest.mark.asyncio
# async def test_update_admin_super_admin_success(http_client_test, super_admin_token, test_new_admin_data):
#     """ Test Case: Updates Admin's Email and Mobile Successfully """
#     from app.database.configuration import DatabaseConfiguration
#
#     admin = await DatabaseConfiguration().user_collection.find_one({
#         "user_type": "admin", "email": test_new_admin_data.get("email")
#     })
#     target_admin = str(admin.get("_id"))
#     payload = {
#         "email": "new_unique_email@example.com",
#         "mobile_number": "9123456780"
#     }
#     response = await http_client_test.put(
#         f"/admin/update_admin?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         params={"admin_id": target_admin},
#         json=payload
#     )
#     assert response.status_code == 200
#     assert response.json() == {"message": "Admin Updated Successfully"}
#     # Verify in DB
#     updated = await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(str(admin["_id"]))})
#     assert updated["email"] == payload["email"]
#     assert updated["user_name"] == payload["email"]
#     assert updated["mobile_number"] == payload["mobile_number"]


#########################################################################
# Test Cases for Deactivate Admin
########################################################################


# Test Case: Deactivate Admin Without Authentication
@pytest.mark.asyncio
async def test_deactivate_admin_unauthenticated(http_client_test):
    """ Test Case: Deactivate Admin Without Authentication """
    response = await http_client_test.put(
        f"/admin/deactivate/123456789012345678901234?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Deactivate Admin With Invalid Token
@pytest.mark.asyncio
async def test_deactivate_admin_invalid_token(http_client_test):
    """ Test Case: Deactivate Admin With Invalid Token """
    response = await http_client_test.put(
        f"/admin/deactivate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Deactivate Admin When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_deactivate_admin_permission_denied(http_client_test, access_token):
    """ Test Case: Deactivate Admin When User Has Insufficient Permissions """
    # Only Super Admin may deactivate
    response = await http_client_test.put(
        f"/admin/deactivate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Deactivate Admin With Invalid Id Format
@pytest.mark.asyncio
async def test_deactivate_admin_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Deactivate Admin With Invalid Id Format """
    response = await http_client_test.put(
        f"/admin/deactivate/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin id"}


# Test Case: Deactivate Admin Not Found
@pytest.mark.asyncio
async def test_deactivate_admin_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Deactivate Admin Not Found """
    fake_id = ObjectId()
    response = await http_client_test.put(
        f"/admin/deactivate/{fake_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404


# Test Case: Successfully Deactivate Admin
@pytest.mark.asyncio
async def test_deactivate_admin_success(http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Successfully Deactivate Admin """
    from app.database.configuration import DatabaseConfiguration
    admin = await DatabaseConfiguration().user_collection.find_one({
        "user_type": "admin"
    })
    admin_id = str(admin.get("_id"))
    response = await http_client_test.put(
        f"/admin/deactivate/{admin_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Admin Deactivated Successfully"}
    # Verify in DB
    updated = await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(admin_id)})
    assert updated["is_activated"] is False


# Test Case: Deactivate Admin Already Deactivated
@pytest.mark.asyncio
async def test_deactivate_admin_already_deactivated(http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Deactivate Admin Already Deactivated """
    from app.database.configuration import DatabaseConfiguration
    admin = await DatabaseConfiguration().user_collection.find_one({
        "user_type": "admin"
    })
    admin_id = str(admin.get("_id"))
    response = await http_client_test.put(
        f"/admin/deactivate/{admin_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Admin Already Deactivated"}



#########################################################################
# Test Cases for Activate Admin
########################################################################


# Test Case: Activate Admin Without Authentication
@pytest.mark.asyncio
async def test_activate_admin_unauthenticated(http_client_test):
    """ Test Case: Activate Admin Without Authentication """
    response = await http_client_test.put(
        f"/admin/activate/123456789012345678901234?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Activate Admin With Invalid Token
@pytest.mark.asyncio
async def test_activate_admin_invalid_token(http_client_test):
    """ Test Case: Activate Admin With Invalid Token """
    response = await http_client_test.put(
        f"/admin/activate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Activate Admin When User Has Insufficient Permissions
@pytest.mark.asyncio
async def test_activate_admin_permission_denied(http_client_test, access_token):
    """ Test Case: Activate Admin When User Has Insufficient Permissions """
    # Only Super Admin may deactivate
    response = await http_client_test.put(
        f"/admin/activate/123456789012345678901234?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Activate Admin With Invalid Id Format
@pytest.mark.asyncio
async def test_activate_admin_invalid_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Activate Admin With Invalid Id Format """
    response = await http_client_test.put(
        f"/admin/activate/invalid_id?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin id"}


# Test Case: Activate Admin Not Found
@pytest.mark.asyncio
async def test_activate_admin_not_found(http_client_test, college_super_admin_access_token):
    """ Test Case: Activate Admin Not Found """
    fake_id = ObjectId()
    response = await http_client_test.put(
        f"/admin/activate/{fake_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404


# Test Case: Successfully Activate Admin
@pytest.mark.asyncio
async def test_activate_admin_success(http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Successfully Activate Admin """
    from app.database.configuration import DatabaseConfiguration
    admin = await DatabaseConfiguration().user_collection.find_one({
        "user_type": "admin"
    })
    admin_id = str(admin.get("_id"))
    response = await http_client_test.put(
        f"/admin/activate/{admin_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Admin Activated Successfully"}
    # Verify in DB
    updated = await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(admin_id)})
    assert updated["is_activated"] is True


# Test Case: Activate Admin Already Activated
@pytest.mark.asyncio
async def test_activate_admin_already_activated(http_client_test, college_super_admin_access_token, test_new_admin_data):
    """ Test Case: Activate Admin Already Activated """
    from app.database.configuration import DatabaseConfiguration
    admin = await DatabaseConfiguration().user_collection.find_one({
        "user_type": "admin"
    })
    admin_id = str(admin.get("_id"))
    response = await http_client_test.put(
        f"/admin/activate/{admin_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Admin Already Activated"}