"""Unit tests for DatasetManager."""
from pathlib import Path

import pytest

from backend.infrastructure.training.dataset import DatasetManager


@pytest.fixture
def tmp_datasets(tmp_path):
    return DatasetManager(tmp_path / "datasets")


@pytest.fixture
def sample_jsonl(tmp_path) -> Path:
    p = tmp_path / "sample.jsonl"
    p.write_text(
        '{"text": "Hello world"}\n{"text": "Fine tuning is fun"}\n',
        encoding="utf-8",
    )
    return p


def test_ingest_creates_version(tmp_datasets, sample_jsonl):
    dv = tmp_datasets.ingest("test-ds", sample_jsonl, split="train")
    assert dv.num_samples == 2
    assert dv.dataset_name == "test-ds"
    assert dv.split == "train"
    assert dv.checksum


def test_list_datasets(tmp_datasets, sample_jsonl):
    tmp_datasets.ingest("ds-a", sample_jsonl)
    tmp_datasets.ingest("ds-b", sample_jsonl)
    names = tmp_datasets.list_datasets()
    assert "ds-a" in names
    assert "ds-b" in names


def test_list_versions(tmp_datasets, sample_jsonl):
    tmp_datasets.ingest("ds", sample_jsonl, split="train")
    tmp_datasets.ingest("ds", sample_jsonl, split="eval")
    versions = tmp_datasets.list_versions("ds")
    splits = {v.split for v in versions}
    assert {"train", "eval"} == splits


def test_iter_samples_jsonl(tmp_datasets, sample_jsonl):
    dv = tmp_datasets.ingest("ds", sample_jsonl)
    texts = list(tmp_datasets.iter_samples(dv))
    assert len(texts) == 2
    assert "Hello world" in texts[0]


def test_iter_samples_txt(tmp_datasets, tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("line one\nline two\nline three\n")
    dv = tmp_datasets.ingest("txt-ds", p)
    texts = list(tmp_datasets.iter_samples(dv))
    assert len(texts) == 3


def test_delete_version(tmp_datasets, sample_jsonl):
    dv = tmp_datasets.ingest("ds", sample_jsonl)
    tmp_datasets.delete_version("ds", dv.version_id)
    assert tmp_datasets.list_versions("ds") == []
