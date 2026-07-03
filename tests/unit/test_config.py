"""Unit tests for Settings configuration."""

import pytest

from backend.shared.config import Settings, get_settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.port == 8000
    assert s.jwt_algorithm == "HS256"
    assert s.env == "development"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_PORT", "9090")
    s = Settings()
    assert s.port == 9090


def test_get_settings_cached() -> None:
    # lru_cache means same object returned
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
