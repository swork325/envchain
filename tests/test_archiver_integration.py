"""Integration tests for archiver + exporter + snapshot cycle."""

import os
import tempfile

import pytest

from envchain.archiver import Archive
from envchain.chain import EnvChain
from envchain.exporter import export_chain
from envchain.snapshot import capture


def _make_chain(**kwargs) -> EnvChain:
    chain = EnvChain(profile="integration")
    for k, v in kwargs.items():
        chain.add(k, default=v)
    return chain


class TestArchiveSnapshotCycle:
    def test_multiple_profiles_stored_independently(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            dev = _make_chain(DB_HOST="localhost", DB_PORT="5432")
            prod = _make_chain(DB_HOST="prod.db", DB_PORT="5432")
            archive.add(dev, profile="dev")
            archive.add(prod, profile="prod")
            archive.save()

            loaded = Archive.load(path)
            dev_entry = loaded.latest(profile="dev")
            prod_entry = loaded.latest(profile="prod")
            assert dev_entry.snapshot.values["DB_HOST"] == "localhost"
            assert prod_entry.snapshot.values["DB_HOST"] == "prod.db"
        finally:
            os.unlink(path)

    def test_restored_snapshot_exportable_as_dotenv(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(API_KEY="secret", TIMEOUT="30")
            archive.add(chain, profile="staging")
            archive.save()

            loaded = Archive.load(path)
            entry = loaded.latest(profile="staging")
            # Rebuild chain from snapshot values for export
            restored = EnvChain(profile="staging")
            for k, v in entry.snapshot.values.items():
                restored.add(k, default=v)
            dotenv = export_chain(restored, fmt="dotenv")
            assert "API_KEY=secret" in dotenv
            assert "TIMEOUT=30" in dotenv
        finally:
            os.unlink(path)

    def test_archive_grows_with_each_capture(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive = Archive(path=path)
            chain = _make_chain(V="1")
            for _ in range(5):
                archive.add(chain, profile="dev")
            archive.save()
            loaded = Archive.load(path)
            assert len(loaded.entries) == 5
        finally:
            os.unlink(path)

    def test_empty_archive_latest_returns_none(self):
        archive = Archive(path="phantom.gz")
        assert archive.latest() is None
        assert archive.latest(profile="dev") is None
