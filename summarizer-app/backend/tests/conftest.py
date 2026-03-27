import sys
import os
import pytest

# Ensure the summarizer-app directory is on the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from jose import jwt
from backend.app.main import app
from backend.app.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Generate a valid JWT token for testing."""
    payload = {"sub": "test-user"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
