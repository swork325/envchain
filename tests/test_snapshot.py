"""Tests for envchain.snapshot."""

from __future__ import annotations

import json
import os

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.snapshot import (
    Snapshot,
    capture,
    load_snapshot,
    restore_to_env,
    save_snapshot,
)


def _make_chain(*names: str) -> EnvChain:
    chain = EnvChain()
    for name in names:
        chain.add(EnvVar(name))
    return chain


class TestSnapshot:
    def test_repr_contains_profile_and_keys(self):
        snap = Snapshot(profile="prod", captured_at="2024-01-01T00:00:00+00:00", values={"A": "1"})
        r = repr(snap)
        assert "prod" in r
        assert "A" in r

    def test_round_trip_dict(self):
        snap = Snapshot(profile="dev", captured_at="ts", values={"X": "hello"})
        restored = Snapshot.from_dict(snap.to_dict())
        assert restored.profile == snap.profile
        assert restored.values == snap.values
        assert restored.captured_at == snap.captured_at


class TestCapture:
    def test_captures_env_values(self, monkeypatch):
        monkeypatch.setenv("SNAP_A", "alpha")
        monkeypatch.setenv("SNAP_B", "beta")
        chain = _make_chain("SNAP_A", "SNAP_B")
        snap = capture(chain, profile="test")
        assert snap.values["SNAP_A"] == "alpha"
        assert snap.values["SNAP_B"] == "beta"
        assert snap.profile == "test"

    def test_captures_none_for_missing_var(self, monkeypatch):
        monkeypatch.delenv("SNAP_MISSING", raising=False)
        chain = _make_chain("SNAP_MISSING")
        snap = capture(chain)
        assert snap.values["SNAP_MISSING"] is None

    def test_captured_at_is_set(self, monkeypatch):
        chain = _make_chain()
        snap = capture(chain)
        assert snap.captured_at != ""


class TestPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        snap = Snapshot(profile="staging", captured_at="ts", values={"K": "v"})
        path = str(tmp_path / "snap.json")
        save_snapshot(snap, path)
        loaded = load_snapshot(path)
        assert loaded.profile == "staging"
        assert loaded.values == {"K": "v"}

    def test_saved_file_is_valid_json(self, tmp_path):
        snap = Snapshot(profile="x", captured_at="ts", values={"A": "1"})
        path = str(tmp_path / "snap.json")
        save_snapshot(snap, path)
        with open(path) as fh:
            data = json.load(fh)
        assert data["profile"] == "x"


class TestRestoreToEnv:
    def test_sets_env_vars(self, monkeypatch):
        snap = Snapshot(profile="p", captured_at="ts", values={"RESTORE_ME": "yes"})
        monkeypatch.delenv("RESTORE_ME", raising=False)
        restore_to_env(snap)
        assert os.environ["RESTORE_ME"] == "yes"

    def test_removes_none_values(self, monkeypatch):
        monkeypatch.setenv("GONE_VAR", "old")
        snap = Snapshot(profile="p", captured_at="ts", values={"GONE_VAR": None})
        restore_to_env(snap)
        assert "GONE_VAR" not in os.environ
