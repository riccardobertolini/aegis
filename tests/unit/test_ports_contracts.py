"""Verify port interfaces are abstract and cannot be instantiated."""
import pytest

from backend.domain.ports.inference import IInferencePort
from backend.domain.ports.knowledge import IKnowledgePort
from backend.domain.ports.memory import IMemoryPort
from backend.domain.ports.security import ISecurityPort
from backend.domain.ports.training import ITrainingPort
from backend.domain.ports.plugin import IPluginPort
from backend.domain.ports.core_ai import ICoreAIPort


@pytest.mark.parametrize("port_cls", [
    IInferencePort,
    IKnowledgePort,
    IMemoryPort,
    ISecurityPort,
    ITrainingPort,
    IPluginPort,
    ICoreAIPort,
])
def test_port_is_abstract(port_cls: type) -> None:
    with pytest.raises(TypeError):
        port_cls()  # type: ignore[abstract]
