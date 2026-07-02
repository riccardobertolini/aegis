"""Unit tests for CheckpointManager (no real PyTorch — mocks state_dict)."""
import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from backend.infrastructure.training.checkpoint import CheckpointManager


@pytest.fixture
def ckpt_mgr(tmp_path):
    return CheckpointManager(tmp_path / "checkpoints")


def test_save_creates_index(ckpt_mgr, tmp_path):
    with patch("backend.infrastructure.training.checkpoint.torch") as mock_torch:
        mock_torch.save = MagicMock()
        ckpt_mgr.save(MagicMock(), "run-1", 50, {"loss": 2.3})
        infos = ckpt_mgr.list_checkpoints("run-1")
    assert len(infos) == 1
    assert infos[0].step == 50


def test_list_empty_run(ckpt_mgr):
    assert ckpt_mgr.list_checkpoints("nonexistent") == []


def test_delete_run(ckpt_mgr, tmp_path):
    with patch("backend.infrastructure.training.checkpoint.torch") as mock_torch:
        mock_torch.save = MagicMock()
        ckpt_mgr.save(MagicMock(), "run-x", 10, {})
    ckpt_mgr.delete_run("run-x")
    assert ckpt_mgr.list_checkpoints("run-x") == []
