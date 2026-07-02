"""Checkpoint manager: save/load/list/delete training checkpoints."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CheckpointInfo:
    run_id: str
    step: int
    path: str
    metrics: dict


class CheckpointManager:
    """Saves PyTorch model checkpoints under checkpoints/<run_id>/step_<N>.pt.

    Layout::

        checkpoints/
            <run_id>/
                step_0050.pt
                step_0100.pt
                index.json
    """

    def __init__(self, checkpoints_root: str | Path) -> None:
        self._root = Path(checkpoints_root)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, model: Any, run_id: str, step: int, metrics: dict) -> str:
        import torch
        run_dir = self._root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        ckpt_name = f"step_{step:06d}.pt"
        ckpt_path = run_dir / ckpt_name
        torch.save(model.state_dict(), str(ckpt_path))

        # Update index
        index_path = run_dir / "index.json"
        index: list[dict] = []
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        index.append({"step": step, "path": str(ckpt_path), "metrics": metrics})
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)

        logger.info("Checkpoint saved: %s", ckpt_path)
        return str(ckpt_path)

    def load(self, model: Any, run_id: str, step: int | None = None) -> Any:
        """Load checkpoint into model. If step is None, loads the latest."""
        import torch
        infos = self.list_checkpoints(run_id)
        if not infos:
            raise FileNotFoundError(f"No checkpoints found for run '{run_id}'")
        if step is None:
            info = max(infos, key=lambda x: x.step)
        else:
            matching = [i for i in infos if i.step == step]
            if not matching:
                raise FileNotFoundError(f"Checkpoint step={step} not found for run '{run_id}'")
            info = matching[0]

        state = torch.load(info.path, map_location="cpu", weights_only=True)
        model.load_state_dict(state, strict=False)
        logger.info("Checkpoint loaded: %s", info.path)
        return model

    def list_checkpoints(self, run_id: str) -> list[CheckpointInfo]:
        index_path = self._root / run_id / "index.json"
        if not index_path.exists():
            return []
        with open(index_path) as f:
            index = json.load(f)
        return [
            CheckpointInfo(run_id=run_id, step=e["step"], path=e["path"], metrics=e["metrics"])
            for e in index
        ]

    def delete_run(self, run_id: str) -> None:
        import shutil
        run_dir = self._root / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
            logger.info("Checkpoints deleted for run '%s'", run_id)
