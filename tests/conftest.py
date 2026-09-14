import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
