"""Unit tests — DatasetManager."""
import json
from pathlib import Path

import pytest

from backend.infrastructure.training.dataset import DatasetManager


def _write_jsonl(path: Path, samples: list[str]) -> None:
    with open(path, "w") as f:
        for s in samples:
            f.write(json.dumps({"text": s}) + "\n")


def test_load_jsonl(tmp_path):
    p = tmp_path / "data.jsonl"
    _write_jsonl(p, ["hello", "world", "foo"])
    mgr = DatasetManager(tmp_path)
    texts = mgr.load_texts(p)
    assert texts == ["hello", "world", "foo"]


def test_load_txt(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("line one\nline two\nline three\n")
    mgr = DatasetManager(tmp_path)
    texts = mgr.load_texts(p)
    assert len(texts) == 3


def test_split_ratios(tmp_path):
    p = tmp_path / "data.jsonl"
    _write_jsonl(p, [f"sample {i}" for i in range(100)])
    mgr = DatasetManager(tmp_path)
    texts = mgr.load_texts(p)
    split = mgr.split(texts, val_ratio=0.1, test_ratio=0.05, seed=0)
    assert len(split.train) + len(split.val) + len(split.test) == 100
    assert len(split.val) >= 1
    assert len(split.test) >= 1


def test_sha256_sidecar(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("some content")
    mgr = DatasetManager(tmp_path)
    sha = mgr.compute_sha256(p)
    assert len(sha) == 64
    assert mgr.verify_sha256(p)


def test_missing_file(tmp_path):
    mgr = DatasetManager(tmp_path)
    with pytest.raises(FileNotFoundError):
        mgr.load_texts(tmp_path / "nonexistent.jsonl")
