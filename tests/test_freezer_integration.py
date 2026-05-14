"""Integration tests: freeze -> persist -> thaw -> re-freeze -> diff."""

import json
from pathlib import Path

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.freezer import freeze, thaw, diff_frozen, FrozenChain
from envchain.exporter import export_chain


def _make_chain(*pairs) -> EnvChain:
    chain = EnvChain()
    for key, default in pairs:
        chain.add(EnvVar(key=key, default=default))
    return chain


class TestFreezeThawCycle:
    def test_values_preserved_through_full_cycle(self):
        chain = _make_chain(("API_KEY", "secret"), ("TIMEOUT", "30"))
        fc = freeze(chain, profile="prod")
        restored = thaw(fc)
        assert restored._vars[0].resolve() == "secret"
        assert restored._vars[1].resolve() == "30"

    def test_frozen_json_file_round_trip(self, tmp_path):
        chain = _make_chain(("DB_HOST", "db.local"), ("DB_PORT", "5432"))
        fc = freeze(chain, profile="staging")
        p = tmp_path / "frozen.json"
        p.write_text(fc.to_json())
        loaded = FrozenChain.from_json(p.read_text())
        assert loaded == fc

    def test_thawed_chain_exportable_as_dotenv(self):
        fc = FrozenChain(profile="dev", values={"HOST": "localhost", "PORT": "8080"})
        chain = thaw(fc)
        output = export_chain(chain, fmt="dotenv")
        assert "HOST=localhost" in output
        assert "PORT=8080" in output

    def test_thawed_chain_exportable_as_json(self):
        fc = FrozenChain(profile="dev", values={"X": "42"})
        chain = thaw(fc)
        output = export_chain(chain, fmt="json")
        data = json.loads(output)
        assert data["X"] == "42"


class TestDiffFrozenIntegration:
    def test_no_changes_between_identical_cycles(self):
        chain = _make_chain(("A", "1"), ("B", "2"))
        fc1 = freeze(chain, profile="dev")
        fc2 = freeze(chain, profile="dev")
        assert diff_frozen(fc1, fc2) == []

    def test_added_key_detected(self):
        before = _make_chain(("A", "1"))
        after = _make_chain(("A", "1"), ("B", "2"))
        fc1 = freeze(before, profile="dev")
        fc2 = freeze(after, profile="dev")
        entries = diff_frozen(fc1, fc2)
        assert any(e.key == "B" for e in entries)

    def test_removed_key_detected(self):
        before = _make_chain(("A", "1"), ("B", "2"))
        after = _make_chain(("A", "1"))
        fc1 = freeze(before, profile="dev")
        fc2 = freeze(after, profile="dev")
        entries = diff_frozen(fc1, fc2)
        assert any(e.key == "B" and e.is_missing_right() for e in entries)

    def test_modified_value_detected(self):
        before = _make_chain(("URL", "http://old.example.com"))
        after = _make_chain(("URL", "http://new.example.com"))
        fc1 = freeze(before, profile="dev")
        fc2 = freeze(after, profile="dev")
        entries = diff_frozen(fc1, fc2)
        assert len(entries) == 1
        assert entries[0].is_value_diff()
