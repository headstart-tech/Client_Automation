import pytest


@pytest.mark.asyncio
async def test_read_root(http_client_test, setup_module):
    """
    Test case -> for check application working or not
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/")
    assert response.status_code == 200
