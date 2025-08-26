import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_set_urls_no_authentication(http_client_test, college_urls, test_college_validation):
    """
    Test set url without authentication
    """

    response = await http_client_test.post(
        f"/college/{str(test_college_validation.get('_id'))}/set_urls?feature_key={feature_key}",
        json=college_urls
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_set_urls_bad_credentials(http_client_test, college_urls, test_college_validation):
    """
    Test set url with bad credentials
    """

    response = await http_client_test.post(
        f"/college/{str(test_college_validation.get('_id'))}/set_urls?feature_key={feature_key}",
        json=college_urls,
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_set_urls_no_permission(http_client_test, college_urls, access_token, test_college_validation):
    """
    Test set url without permission
    """

    response = await http_client_test.post(
        f"/college/{str(test_college_validation.get('_id'))}/set_urls?feature_key={feature_key}",
        json=college_urls,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_set_urls(http_client_test, college_urls, college_super_admin_access_token, test_college_validation):
    """
    Test set url
    """

    response = await http_client_test.post(
        f"/college/{str(test_college_validation.get('_id'))}/set_urls?feature_key={feature_key}",
        json=college_urls,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_urls_no_authentication(http_client_test, test_college_validation):
    """
    Test get url without authentication
    """

    response = await http_client_test.get(
        f"/college/{str(test_college_validation.get('_id'))}/urls?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_urls_bad_credentials(http_client_test, test_college_validation):
    """
    Test get url with bad credentials
    """

    response = await http_client_test.get(
        f"/college/{str(test_college_validation.get('_id'))}/urls?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_urls_no_permission(http_client_test, access_token, test_college_validation):
    """
    Test set url without permission
    """

    response = await http_client_test.get(
        f"/college/{str(test_college_validation.get('_id'))}/urls?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_urls(http_client_test, college_super_admin_access_token, test_college_validation):
    """
    Test set url
    """

    response = await http_client_test.get(
        f"/college/{str(test_college_validation.get('_id'))}/urls?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200