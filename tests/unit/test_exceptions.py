"""Unit tests for domain exception hierarchy."""
from backend.shared.exceptions import (
    AegisBaseError,
    AuthenticationError,
    ModelNotFoundError,
)


def test_base_error_message() -> None:
    err = AegisBaseError("something went wrong", key="value")
    assert str(err) == "something went wrong"
    assert err.context == {"key": "value"}


def test_model_not_found_is_base_error() -> None:
    err = ModelNotFoundError("model xyz not found", model_id="xyz")
    assert isinstance(err, AegisBaseError)
    assert err.context["model_id"] == "xyz"


def test_auth_error_hierarchy() -> None:
    err = AuthenticationError("invalid credentials")
    assert isinstance(err, AegisBaseError)
