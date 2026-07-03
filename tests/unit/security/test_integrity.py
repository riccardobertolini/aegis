"""Unit tests: model file integrity hashing."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.infrastructure.security.integrity import ModelIntegrityService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_register_creates_hash(tmp_path, mock_session):
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(b"fake model weights" * 100)
    mock_session.get = AsyncMock(return_value=None)
    svc = ModelIntegrityService(mock_session)
    h = await svc.register("model-1", str(model_file))
    assert len(h) == 64  # SHA-256 hex
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_verify_detects_tampering(tmp_path, mock_session):
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(b"original")
    # Simulate stored hash of different content
    from backend.infrastructure.security.models import ModelHashModel
    stored = ModelHashModel(
        model_id="m1",
        hash_value="aabbcc" * 10 + "aabb",  # wrong hash
        algorithm="sha256",
    )
    mock_session.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=stored)))
    ))
    svc = ModelIntegrityService(mock_session)
    result = await svc.verify("m1", str(model_file))
    assert result.is_valid is False
