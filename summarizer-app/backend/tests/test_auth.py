import pytest
from jose import jwt
from backend.app.config import settings
from backend.app.api import verify_token
from backend.app.errors import AuthenticationError
from unittest.mock import MagicMock


class TestJWTAuthentication:
    """Tests for JWT token verification."""

    def test_valid_token(self):
        payload = {"sub": "user123"}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        credentials = MagicMock()
        credentials.credentials = token
        result = verify_token(credentials)
        assert result == "user123"

    def test_invalid_token(self):
        credentials = MagicMock()
        credentials.credentials = "invalid-token-string"
        with pytest.raises(AuthenticationError):
            verify_token(credentials)

    def test_token_wrong_secret(self):
        payload = {"sub": "user123"}
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        credentials = MagicMock()
        credentials.credentials = token
        with pytest.raises(AuthenticationError):
            verify_token(credentials)

    def test_token_missing_sub(self):
        payload = {"name": "user123"}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        credentials = MagicMock()
        credentials.credentials = token
        with pytest.raises(AuthenticationError):
            verify_token(credentials)

    def test_expired_token_structure(self):
        """Token with wrong algorithm should fail."""
        payload = {"sub": "user123"}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS384")
        credentials = MagicMock()
        credentials.credentials = token
        with pytest.raises(AuthenticationError):
            verify_token(credentials)

    def test_api_rejects_missing_auth(self, client):
        response = client.post("/api/summarize", data={"text": "test"})
        assert response.status_code in [401, 403]

    def test_api_rejects_bad_token(self, client):
        response = client.post(
            "/api/summarize",
            data={"text": "test"},
            headers={"Authorization": "Bearer bad-token"},
        )
        assert response.status_code == 401
