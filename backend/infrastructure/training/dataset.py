"""Dataset manager — local JSONL/TXT datasets with versioning."""
from __future__ import annotations

import hashlib
import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    name: str
    path: Path
    num_samples: int
    sha256: str
    format: str  # "jsonl" | "txt"
    split: str   # "train" | "val" | "test"


@dataclass
class DatasetSplit:
    train: list[str]
    val: list[str]
    test: list[str]


class DatasetManager:
    """
    Manages local datasets stored as JSONL or plain TXT files.

    JSONL format (one JSON per line)::

        {"text": "..."}
        {"text": "...", "label": "..."}

    TXT format: one sample per line (non-empty lines).

    Versioning: sha256 of the file content is stored in a sidecar
    <dataset>.sha256 file next to the data file.
    """

    def __init__(self, datasets_root: Path) -> None:
        self._root = datasets_root
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_datasets(self) -> list[DatasetInfo]:
        infos: list[DatasetInfo] = []
        for p in sorted(self._root.rglob("*.jsonl")):
            infos.append(self._stat(p, "jsonl"))
        for p in sorted(self._root.rglob("*.txt")):
            if not p.name.endswith(".sha256"):
                infos.append(self._stat(p, "txt"))
        return infos

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_texts(self, path: str | Path) -> list[str]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {p}")
        if p.suffix == ".jsonl":
            return self._load_jsonl(p)
        return self._load_txt(p)

    def split(
        self,
        texts: list[str],
        val_ratio: float = 0.1,
        test_ratio: float = 0.05,
        seed: int = 42,
    ) -> DatasetSplit:
        rng = random.Random(seed)
        data = texts[:]
        rng.shuffle(data)
        n = len(data)
        n_test = max(1, int(n * test_ratio))
        n_val = max(1, int(n * val_ratio))
        return DatasetSplit(
            test=data[:n_test],
            val=data[n_test : n_test + n_val],
            train=data[n_test + n_val :],
        )

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    def compute_sha256(self, path: str | Path) -> str:
        p = Path(path)
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        digest = h.hexdigest()
        sidecar = p.with_suffix(p.suffix + ".sha256")
        sidecar.write_text(digest)
        return digest

    def verify_sha256(self, path: str | Path) -> bool:
        p = Path(path)
        sidecar = p.with_suffix(p.suffix + ".sha256")
        if not sidecar.exists():
            return False
        expected = sidecar.read_text().strip()
        return self.compute_sha256(p) == expected

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load_jsonl(self, path: Path) -> list[str]:
        texts: list[str] = []
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    texts.append(obj.get("text") or obj.get("content") or str(obj))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed JSONL line %d in %s", i, path)
        return texts

    def _load_txt(self, path: Path) -> list[str]:
        with open(path, encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f if line.strip()]

    def _stat(self, path: Path, fmt: str) -> DatasetInfo:
        texts = self.load_texts(path)
        sidecar = path.with_suffix(path.suffix + ".sha256")
        sha = sidecar.read_text().strip() if sidecar.exists() else self.compute_sha256(path)
        split_name = "train"
        for part in ("val", "valid", "test", "dev"):
            if part in path.stem.lower():
                split_name = part
                break
        return DatasetInfo(
            name=path.stem,
            path=path,
            num_samples=len(texts),
            sha256=sha,
            format=fmt,
            split=split_name,
        )
