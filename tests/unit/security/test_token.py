"""Unit tests: JWT token creation and verification."""
import time
import pytest
from unittest.mock import patch, MagicMock

from backend.infrastructure.security.token import (
    create_access_token, decode_access_token, hash_token
)
from backend.shared.exceptions import AuthenticationError


@pytest.fixture(autouse=True)
def _mock_settings(monkeypatch):
    settings = MagicMock()
    settings.jwt_secret_key = "test-secret-key-32-chars-minimum!"
    with patch("backend.infrastructure.security.token.get_settings", return_value=settings):
        yield


def test_create_and_decode_token():
    token, expires_at = create_access_token(
        user_id="u1", username="alice",
        roles=["viewer"], permissions=["model:read"],
        session_id="sess1",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "u1"
    assert payload["username"] == "alice"
    assert payload["roles"] == ["viewer"]
    assert payload["session_id"] == "sess1"


def test_expired_token_raises():
    token, _ = create_access_token(
        user_id="u1", username="alice",
        roles=[], permissions=[], session_id="s",
        expiry_minutes=-1,  # already expired
    )
    with pytest.raises(AuthenticationError, match="expired"):
        decode_access_token(token)


def test_tampered_token_raises():
    token, _ = create_access_token(
        user_id="u1", username="alice",
        roles=[], permissions=[], session_id="s",
    )
    with pytest.raises(AuthenticationError):
        decode_access_token(token + "tampered")


def test_hash_token_deterministic():
    t = "mytoken"
    assert hash_token(t) == hash_token(t)
    assert hash_token(t) != hash_token(t + "x")
