"""Dataset manager: local JSONL/CSV/TXT ingestion, versioning, preprocessing.

No network calls. All data stays in datasets/ directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class DatasetVersion:
    version_id: str
    dataset_name: str
    path: Path
    num_samples: int
    checksum: str
    created_at: str
    format: str  # "jsonl" | "csv" | "txt"
    split: str   # "train" | "eval" | "test"
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "dataset_name": self.dataset_name,
            "path": str(self.path),
            "num_samples": self.num_samples,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "format": self.format,
            "split": self.split,
            "meta": self.meta,
        }


class DatasetManager:
    """Manages local training datasets with versioning.

    Layout::

        datasets/
            my-dataset/
                v1/
                    train.jsonl
                    eval.jsonl
                    meta.json
                v2/
                    ...
    """

    def __init__(self, datasets_root: str | Path) -> None:
        self._root = Path(datasets_root)
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(
        self,
        name: str,
        source_path: str | Path,
        split: str = "train",
        meta: dict | None = None,
    ) -> DatasetVersion:
        """Copy source file into versioned dataset directory."""
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source dataset not found: {src}")

        fmt = self._detect_format(src)
        version_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        version_dir = self._root / name / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        dest = version_dir / f"{split}.{fmt}"
        shutil.copy2(src, dest)

        checksum = self._sha256(dest)
        samples = self._count_samples(dest, fmt)

        dv = DatasetVersion(
            version_id=version_id,
            dataset_name=name,
            path=dest,
            num_samples=samples,
            checksum=checksum,
            created_at=version_id,
            format=fmt,
            split=split,
            meta=meta or {},
        )
        # Persist metadata
        meta_path = version_dir / "meta.json"
        existing: list[dict] = []
        if meta_path.exists():
            with open(meta_path) as f:
                existing = json.load(f)
        existing.append(dv.to_dict())
        with open(meta_path, "w") as f:
            json.dump(existing, f, indent=2)

        logger.info("Dataset '%s' v%s ingested — %d samples", name, version_id, samples)
        return dv

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_datasets(self) -> list[str]:
        if not self._root.exists():
            return []
        return [d.name for d in sorted(self._root.iterdir()) if d.is_dir()]

    def list_versions(self, name: str) -> list[DatasetVersion]:
        dataset_dir = self._root / name
        if not dataset_dir.exists():
            return []
        versions: list[DatasetVersion] = []
        for v_dir in sorted(dataset_dir.iterdir()):
            meta_path = v_dir / "meta.json"
            if not meta_path.exists():
                continue
            with open(meta_path) as f:
                entries = json.load(f)
            for e in entries:
                versions.append(DatasetVersion(
                    version_id=e["version_id"],
                    dataset_name=e["dataset_name"],
                    path=Path(e["path"]),
                    num_samples=e["num_samples"],
                    checksum=e["checksum"],
                    created_at=e["created_at"],
                    format=e["format"],
                    split=e["split"],
                    meta=e.get("meta", {}),
                ))
        return versions

    def get_latest_version(self, name: str, split: str = "train") -> DatasetVersion | None:
        versions = [v for v in self.list_versions(name) if v.split == split]
        return versions[-1] if versions else None

    def delete_version(self, name: str, version_id: str) -> None:
        version_dir = self._root / name / version_id
        if version_dir.exists():
            shutil.rmtree(version_dir)
            logger.info("Deleted dataset '%s' version '%s'", name, version_id)

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def iter_samples(
        self,
        version: DatasetVersion,
        text_field: str = "text",
    ) -> Iterator[str]:
        """Yield text strings from dataset file."""
        if version.format == "jsonl":
            yield from self._iter_jsonl(version.path, text_field)
        elif version.format == "csv":
            yield from self._iter_csv(version.path, text_field)
        else:
            yield from self._iter_txt(version.path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_format(path: Path) -> str:
        suffix = path.suffix.lower().lstrip(".")
        if suffix in ("jsonl", "json"):
            return "jsonl"
        if suffix == "csv":
            return "csv"
        return "txt"

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _count_samples(path: Path, fmt: str) -> int:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [l for l in f if l.strip()]
        return len(lines)

    @staticmethod
    def _iter_jsonl(path: Path, text_field: str) -> Iterator[str]:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield obj.get(text_field, "")
                    else:
                        yield str(obj)
                except json.JSONDecodeError:
                    yield line

    @staticmethod
    def _iter_csv(path: Path, text_field: str) -> Iterator[str]:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row.get(text_field, " ".join(row.values()))

    @staticmethod
    def _iter_txt(path: Path) -> Iterator[str]:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line
