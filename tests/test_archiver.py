"""Tests for envchain.archiver."""

import gzip
import json
import os
import tempfile

import pytest

from envchain.archiver import Archive, ArchiveEntry
from envchain.chain import EnvChain
from envchain.snapshot import Snapshot


def _make_chain(**kwargs) -> EnvChain:
    chain = EnvChain(profile="test")
    for k, v in kwargs.items():
        chain.add(k, default=v)
    return chain


class TestArchiveEntry:
    def test_to_dict_round_trip(self):
        chain = _make_chain(FOO="bar", BAZ="qux")
        from envchain.snapshot import capture
        snap = capture(chain, profile="dev")
        entry = ArchiveEntry(timestamp="2024-01-01T00:00:00+00:00", profile="dev", snapshot=snap)
        data = entry.to_dict()
        restored = ArchiveEntry.from_dict(data)
        assert restored.timestamp == entry.timestamp
        assert restored.profile == entry.profile
        assert restored.snapshot.values == entry.snapshot.values

    def test_from_dict_preserves_profile(self):
        chain = _make_chain(X="1")
        from envchain.snapshot import capture
        snap = capture(chain, profile="staging")
        entry = ArchiveEntry(timestamp="t", profile="staging", snapshot=snap)
        restored = ArchiveEntry.from_dict(entry.to_dict())
        assert restored.profile == "staging"


class TestArchive:
    def test_add_creates_entry(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(A="1", B="2")
            entry = archive.add(chain, profile="prod")
            assert entry.profile == "prod"
            assert len(archive.entries) == 1
        finally:
            os.unlink(path)

    def test_save_and_load_round_trip(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(KEY="value")
            archive.add(chain, profile="dev")
            archive.save()
            loaded = Archive.load(path)
            assert len(loaded.entries) == 1
            assert loaded.entries[0].profile == "dev"
            assert loaded.entries[0].snapshot.values.get("KEY") == "value"
        finally:
            os.unlink(path)

    def test_latest_returns_last_entry(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(K="v")
            archive.add(chain, profile="dev")
            archive.add(chain, profile="prod")
            latest = archive.latest()
            assert latest.profile == "prod"
        finally:
            os.unlink(path)

    def test_latest_filtered_by_profile(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(K="v")
            archive.add(chain, profile="dev")
            archive.add(chain, profile="prod")
            latest = archive.latest(profile="dev")
            assert latest.profile == "dev"
        finally:
            os.unlink(path)

    def test_latest_returns_none_when_empty(self):
        archive = Archive(path="unused.gz")
        assert archive.latest() is None

    def test_saved_file_is_valid_gzip(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(Z="9")
            archive.add(chain, profile="test")
            archive.save()
            with gzip.open(path, "rb") as fh:
                data = json.loads(fh.read())
            assert "entries" in data
        finally:
            os.unlink(path)
