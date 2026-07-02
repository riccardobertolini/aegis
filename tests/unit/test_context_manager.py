"""Unit tests for ContextManager — rolling window and compression."""
import pytest

from backend.domain.model.runtime_config import RuntimeConfig
from backend.infrastructure.adapters.inference.context_manager import ContextManager


@pytest.fixture()
def config() -> RuntimeConfig:
    return RuntimeConfig(
        max_context_length=64,
        enable_context_compression=True,
        compression_ratio=0.5,
    )


class TestContextManager:
    def test_get_or_create(self) -> None:
        cm = ContextManager()
        w = cm.get_or_create("sess-1")
        assert w.session_id == "sess-1"
        assert w.tokens == []

    def test_same_session_same_object(self) -> None:
        cm = ContextManager()
        w1 = cm.get_or_create("sess-1")
        w2 = cm.get_or_create("sess-1")
        assert w1 is w2

    def test_append_grows_tokens(self, config: RuntimeConfig) -> None:
        cm = ContextManager()
        cm.append("s", [1, 2, 3], config)
        assert cm.get_or_create("s").tokens == [1, 2, 3]

    def test_compression_triggered(self, config: RuntimeConfig) -> None:
        cm = ContextManager()
        # Feed 100 tokens — exceeds max_context_length=64
        tokens = list(range(100))
        cm.append("s", tokens, config)
        w = cm.get_or_create("s")
        assert w.effective_length() <= config.max_context_length

    def test_build_prompt_includes_prefix(self, config: RuntimeConfig) -> None:
        cm = ContextManager()
        tokens = list(range(100))
        cm.append("s", tokens, config)
        prompt = cm.build_prompt_ids("s")
        assert len(prompt) > 0

    def test_clear(self, config: RuntimeConfig) -> None:
        cm = ContextManager()
        cm.append("s", [1, 2, 3], config)
        cm.clear("s")
        w = cm.get_or_create("s")
        assert w.tokens == []

    def test_no_compression_when_disabled(self) -> None:
        cfg = RuntimeConfig(max_context_length=32, enable_context_compression=False)
        cm = ContextManager()
        tokens = list(range(50))
        cm.append("s", tokens, cfg)
        # No compression: all tokens kept
        w = cm.get_or_create("s")
        assert len(w.tokens) == 50
