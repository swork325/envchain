"""Tests for envchain.pinner."""

import json
import os

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.pinner import (
    PinEntry,
    PinReport,
    check_pins,
    pin_chain,
    pins_from_json,
    pins_to_json,
)


def _make_chain(*pairs) -> EnvChain:
    chain = EnvChain(profile="test")
    for key, default in pairs:
        chain.add(EnvVar(key, default=default))
    return chain


# ---------------------------------------------------------------------------
# PinEntry
# ---------------------------------------------------------------------------

class TestPinEntry:
    def test_not_drifted_when_values_equal(self):
        e = PinEntry(key="FOO", pinned_value="bar", current_value="bar")
        assert not e.is_drifted

    def test_drifted_when_values_differ(self):
        e = PinEntry(key="FOO", pinned_value="old", current_value="new")
        assert e.is_drifted

    def test_drifted_when_current_is_none(self):
        e = PinEntry(key="FOO", pinned_value="x", current_value=None)
        assert e.is_drifted

    def test_not_drifted_when_both_none(self):
        e = PinEntry(key="FOO", pinned_value=None, current_value=None)
        assert not e.is_drifted


# ---------------------------------------------------------------------------
# PinReport
# ---------------------------------------------------------------------------

class TestPinReport:
    def test_passed_when_no_drift(self):
        entries = [PinEntry("A", "1", "1"), PinEntry("B", "2", "2")]
        report = PinReport(profile="prod", entries=entries)
        assert report.passed

    def test_fails_when_drift_present(self):
        entries = [PinEntry("A", "1", "99")]
        report = PinReport(profile="prod", entries=entries)
        assert not report.passed
        assert len(report.drifted) == 1
        assert len(report.stable) == 0

    def test_stable_and_drifted_partition(self):
        entries = [
            PinEntry("A", "1", "1"),
            PinEntry("B", "2", "changed"),
        ]
        report = PinReport(profile="staging", entries=entries)
        assert len(report.stable) == 1
        assert len(report.drifted) == 1


# ---------------------------------------------------------------------------
# pin_chain
# ---------------------------------------------------------------------------

class TestPinChain:
    def test_captures_default_values(self):
        chain = _make_chain(("KEY_A", "alpha"), ("KEY_B", "beta"))
        pins = pin_chain(chain)
        assert pins == {"KEY_A": "alpha", "KEY_B": "beta"}

    def test_captures_env_override(self, monkeypatch):
        monkeypatch.setenv("OVERRIDE_KEY", "from_env")
        chain = _make_chain(("OVERRIDE_KEY", "default"))
        pins = pin_chain(chain)
        assert pins["OVERRIDE_KEY"] == "from_env"

    def test_none_when_no_default_and_not_set(self):
        chain = _make_chain(("MISSING_KEY", None))
        pins = pin_chain(chain)
        assert pins["MISSING_KEY"] is None


# ---------------------------------------------------------------------------
# check_pins
# ---------------------------------------------------------------------------

class TestCheckPins:
    def test_no_drift_when_values_unchanged(self):
        chain = _make_chain(("X", "hello"))
        pins = pin_chain(chain)
        report = check_pins(chain, pins, profile="dev")
        assert report.passed
        assert report.profile == "dev"

    def test_detects_drift_after_env_change(self, monkeypatch):
        chain = _make_chain(("DRIFTED", "original"))
        pins = {"DRIFTED": "original"}
        monkeypatch.setenv("DRIFTED", "changed")
        report = check_pins(chain, pins)
        assert not report.passed
        assert report.drifted[0].key == "DRIFTED"

    def test_missing_key_in_chain_shows_as_drift(self):
        chain = _make_chain(("PRESENT", "v"))
        pins = {"PRESENT": "v", "GHOST": "old"}
        report = check_pins(chain, pins)
        ghost = next(e for e in report.entries if e.key == "GHOST")
        assert ghost.is_drifted

    def test_entries_sorted_by_key(self):
        chain = _make_chain(("Z_KEY", "z"), ("A_KEY", "a"))
        pins = pin_chain(chain)
        report = check_pins(chain, pins)
        keys = [e.key for e in report.entries]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

class TestPinsJson:
    def test_round_trip(self):
        original = {"FOO": "bar", "BAZ": None}
        assert pins_from_json(pins_to_json(original)) == original

    def test_output_is_valid_json(self):
        raw = pins_to_json({"K": "v"})
        parsed = json.loads(raw)
        assert parsed == {"K": "v"}
