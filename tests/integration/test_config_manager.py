"""Integration tests — ConfigManager (local, no network)."""
from __future__ import annotations

import pytest

from backend.infrastructure.adapters.config_manager import ConfigManager
from backend.infrastructure.adapters.encryption import EncryptionService


@pytest.fixture
def config_mgr(tmp_path):
    enc = EncryptionService(key_dir=str(tmp_path / "keys"))
    return ConfigManager(
        encryption=enc,
        config_dir=str(tmp_path / "config"),
    )


def test_set_and_get_global_config(config_mgr):
    config_mgr.set("global.model_name", "mamba-1.4b")
    assert config_mgr.get("global.model_name") == "mamba-1.4b"


def test_assistant_override(config_mgr):
    config_mgr.set("global.language", "en")
    config_mgr.set("assistant.123.language", "it")
    assert config_mgr.get("global.language") == "en"
    assert config_mgr.get_for_assistant("assistant.language", assistant_id="123") == "it"


def test_feature_flag_default_false(config_mgr):
    assert config_mgr.feature_enabled("speech") is False


def test_feature_flag_enable(config_mgr):
    config_mgr.enable_feature("speech")
    assert config_mgr.feature_enabled("speech") is True


def test_feature_flag_disable(config_mgr):
    config_mgr.enable_feature("translation")
    config_mgr.disable_feature("translation")
    assert config_mgr.feature_enabled("translation") is False


def test_config_persists_across_instances(tmp_path):
    enc = EncryptionService(key_dir=str(tmp_path / "keys"))
    mgr1 = ConfigManager(encryption=enc, config_dir=str(tmp_path / "config"))
    mgr1.set("global.version", "2.0")
    mgr1.save()
    mgr2 = ConfigManager(encryption=enc, config_dir=str(tmp_path / "config"))
    mgr2.load()
    assert mgr2.get("global.version") == "2.0"
