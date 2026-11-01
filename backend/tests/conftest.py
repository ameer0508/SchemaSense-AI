import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_provider import MockAIProvider, set_ai_provider


@pytest.fixture(autouse=True)
def setup_mock_ai():
    """Ensure mock AI provider is active for all unit and API tests."""
    mock_provider = MockAIProvider()
    set_ai_provider(mock_provider)
    yield mock_provider


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client fixture for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client
