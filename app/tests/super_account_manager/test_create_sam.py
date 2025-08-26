""" This File Contains Test Cases Related to Creation Super Account Manager """
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()
@pytest.mark.asyncio
async def test_create_sam_no_authentication(http_client_test, setup_module, test_sam_data):
    """ Test Case To Create Super Account Manager Without Authentication """
    response = await http_client_test.post(
        f"/super_account_manager/create?feature_key={feature_key}",
        json=test_sam_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_create_sam_bad_credentials(http_client_test, setup_module, test_sam_data):
    """ Test Case To Create Super Account Manager With Bad Credentials """
    response = await http_client_test.post(
        f"/super_account_manager/create?feature_key={feature_key}",
        json=test_sam_data,
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_create_sam_bad_credentials_no_permission(http_client_test, setup_module, test_sam_data, access_token):
    """ Test Case To Create Super Account Manager With No Permission """
    response = await http_client_test.post(
        f"/super_account_manager/create?feature_key={feature_key}",
        json=test_sam_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_create_sam(http_client_test, setup_module, test_sam_data, college_super_admin_access_token):
    """ Test Case To Create Super Account Manager """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().user_collection.delete_many({'email': test_sam_data.get('email')})

    response = await http_client_test.post(
        f"/super_account_manager/create?feature_key={feature_key}",
        json=test_sam_data,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

    super_account_manager = await DatabaseConfiguration().user_collection.find_one(
        {
            "email": test_sam_data.get("email")
        }
    )
    assert super_account_manager is not None

@pytest.mark.asyncio
async def test_create_sam_duplicate_email(http_client_test, setup_module, test_sam_data, college_super_admin_access_token):
    """ Test Case To Create Super Account Manager With Duplicate Email """
    response = await http_client_test.post(
        f"/super_account_manager/create?feature_key={feature_key}",
        json=test_sam_data,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Email or Mobile Number already exists"}