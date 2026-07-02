"""Unit tests — CheckpointManager (mocked torch)."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.infrastructure.training.checkpoint_manager import CheckpointManager


def _fake_model(n_params: int = 10):
    m = MagicMock()
    m.state_dict.return_value = {"weight": list(range(n_params))}
    return m


def test_save_and_list(tmp_path):
    with patch("torch.save") as mock_save:
        # simulate torch.save writing a real file
        def fake_save(obj, path, **kw):
            Path(path).write_bytes(b"fake_weights")
        mock_save.side_effect = fake_save

        mgr = CheckpointManager(tmp_path)
        info = mgr.save("job1", step=10, epoch=0, model=_fake_model(),
                        train_loss=1.5, val_loss=1.8)
        assert info.step == 10
        assert (tmp_path / "job1" / "checkpoints" / "step_00000010" / "model.pt").exists()

        ckpts = mgr.list_checkpoints("job1")
        assert len(ckpts) == 1
        assert ckpts[0].step == 10


def test_promote(tmp_path):
    models_root = tmp_path / "models"
    models_root.mkdir()
    experiments_root = tmp_path / "experiments"

    with patch("torch.save") as mock_save, patch("shutil.copy2") as mock_copy:
        def fake_save(obj, path, **kw):
            Path(path).write_bytes(b"fake_weights")
        mock_save.side_effect = fake_save

        mgr = CheckpointManager(experiments_root)
        mgr.save("job1", step=5, epoch=0, model=_fake_model(), train_loss=1.0)

        def fake_copy(src, dst):
            Path(dst).write_bytes(b"fake_weights")
        mock_copy.side_effect = fake_copy

        sha = mgr.promote("job1", step=5, models_root=models_root, target_model_id="my-model-v2")
        assert len(sha) == 64
        assert (models_root / "my-model-v2" / "promotion.json").exists()
