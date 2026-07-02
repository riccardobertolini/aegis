"""Unit tests for RuntimeConfig."""
from backend.domain.model.model_metadata import DeviceTarget, QuantizationLevel
from backend.domain.model.runtime_config import RuntimeConfig


class TestRuntimeConfig:
    def test_defaults(self) -> None:
        cfg = RuntimeConfig()
        assert cfg.device == DeviceTarget.AUTO
        assert cfg.quantization == QuantizationLevel.NONE
        assert cfg.max_context_length == 2048
        assert cfg.max_new_tokens == 512
        assert cfg.use_kv_cache is True

    def test_custom_values(self) -> None:
        cfg = RuntimeConfig(
            device=DeviceTarget.CPU,
            quantization=QuantizationLevel.INT8,
            max_context_length=1024,
            temperature=0.5,
        )
        assert cfg.device == DeviceTarget.CPU
        assert cfg.quantization == QuantizationLevel.INT8
        assert cfg.temperature == 0.5

    def test_from_settings_returns_config(self) -> None:
        cfg = RuntimeConfig.from_settings(object())
        assert isinstance(cfg, RuntimeConfig)
