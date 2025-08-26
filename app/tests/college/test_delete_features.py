"""
This file contains test cases related to delete features.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_features(http_client_test, setup_module, test_college_validation,
                               college_super_admin_access_token, super_admin_access_token):
    """
    Different test cases of get delete features.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        super_admin_access_token: A fixture which create super
            admin if not exist and return access token of super admin.

    Assertions:\n
        response status code and json message.
    """
    # Test case -> not authenticated if user not logged in
    response = await http_client_test.put(f"/college/features/delete/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Test case -> bad token for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Test case -> required college id for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Test case -> invalid college id for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # Test case -> college not found for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    college_id = str(test_college_validation.get('_id'))
    # Test case -> required body for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Body must be required and valid.'}

    # Test case -> no permission for delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=[]
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    # Test case -> feature not found
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Feature not found."}

    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": ObjectId(college_id)}, {"$set": {"features": {"dashboard": {"admin_dashboard": {"test": True}}}}})
    # Test case -> menu not found when delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{"dash": []}]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Menu `dash` not found."}

    # Test case -> menu not found when delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{}]
    )
    assert response.status_code == 200
    assert response.json() == {'detail': 'Feature not deleted.'}

    # Test case -> wong sub-menu information when delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{"dashboard": []}]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Sub menu information should be in the dictionary format."}

    # Test case -> sub-menu not found when delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{"dashboard": {"test": []}}]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Sub menu `test` not found inside menu `dashboard`."}

    # Test case -> pass delete feature information in wrong format when delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{"dashboard": {"admin_dashboard": {}}}]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Deleted features should be in the list format."}

    # Test case -> delete features
    response = await http_client_test.put(
        f"/college/features/delete/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=[{"dashboard": {"admin_dashboard": ["test"]}}]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Feature deleted."}
