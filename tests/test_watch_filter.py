"""Tests for envchain.watch_filter — key, prefix, and kind filters for ChangeEvents."""

import pytest

from envchain.watcher import ChangeEvent
from envchain.watch_filter import key_filter, prefix_filter, kind_filter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _added(key: str, value: str = "val") -> ChangeEvent:
    return ChangeEvent(key=key, before=None, after=value)


def _removed(key: str, value: str = "val") -> ChangeEvent:
    return ChangeEvent(key=key, before=value, after=None)


def _modified(key: str, before: str = "old", after: str = "new") -> ChangeEvent:
    return ChangeEvent(key=key, before=before, after=after)


# ---------------------------------------------------------------------------
# key_filter
# ---------------------------------------------------------------------------

class TestKeyFilter:
    def test_keeps_matching_key(self):
        events = [_added("DB_HOST"), _added("API_KEY")]
        result = key_filter(events, keys=["DB_HOST"])
        assert [e.key for e in result] == ["DB_HOST"]

    def test_keeps_multiple_matching_keys(self):
        events = [_added("DB_HOST"), _added("API_KEY"), _added("SECRET")]
        result = key_filter(events, keys=["DB_HOST", "SECRET"])
        assert {e.key for e in result} == {"DB_HOST", "SECRET"}

    def test_empty_keys_returns_nothing(self):
        events = [_added("DB_HOST"), _added("API_KEY")]
        result = key_filter(events, keys=[])
        assert list(result) == []

    def test_no_matching_keys_returns_nothing(self):
        events = [_added("DB_HOST")]
        result = key_filter(events, keys=["MISSING"])
        assert list(result) == []

    def test_empty_event_list(self):
        result = key_filter([], keys=["DB_HOST"])
        assert list(result) == []


# ---------------------------------------------------------------------------
# prefix_filter
# ---------------------------------------------------------------------------

class TestPrefixFilter:
    def test_keeps_events_with_matching_prefix(self):
        events = [_added("DB_HOST"), _added("DB_PORT"), _added("API_KEY")]
        result = prefix_filter(events, prefix="DB_")
        assert {e.key for e in result} == {"DB_HOST", "DB_PORT"}

    def test_no_match_returns_empty(self):
        events = [_added("API_KEY"), _added("SECRET")]
        result = prefix_filter(events, prefix="DB_")
        assert list(result) == []

    def test_empty_prefix_matches_all(self):
        events = [_added("DB_HOST"), _added("API_KEY")]
        result = prefix_filter(events, prefix="")
        assert len(list(result)) == 2

    def test_prefix_is_case_sensitive(self):
        events = [_added("db_host"), _added("DB_HOST")]
        result = prefix_filter(events, prefix="DB_")
        assert [e.key for e in result] == ["DB_HOST"]

    def test_empty_event_list(self):
        result = prefix_filter([], prefix="DB_")
        assert list(result) == []


# ---------------------------------------------------------------------------
# kind_filter
# ---------------------------------------------------------------------------

class TestKindFilter:
    def test_keeps_added_events(self):
        events = [_added("A"), _removed("B"), _modified("C")]
        result = kind_filter(events, kinds=["added"])
        assert [e.key for e in result] == ["A"]

    def test_keeps_removed_events(self):
        events = [_added("A"), _removed("B"), _modified("C")]
        result = kind_filter(events, kinds=["removed"])
        assert [e.key for e in result] == ["B"]

    def test_keeps_modified_events(self):
        events = [_added("A"), _removed("B"), _modified("C")]
        result = kind_filter(events, kinds=["modified"])
        assert [e.key for e in result] == ["C"]

    def test_keeps_multiple_kinds(self):
        events = [_added("A"), _removed("B"), _modified("C")]
        result = kind_filter(events, kinds=["added", "removed"])
        assert {e.key for e in result} == {"A", "B"}

    def test_empty_kinds_returns_nothing(self):
        events = [_added("A"), _removed("B")]
        result = kind_filter(events, kinds=[])
        assert list(result) == []

    def test_raises_for_unknown_kind(self):
        with pytest.raises(ValueError, match="unknown kind"):
            kind_filter([_added("A")], kinds=["changed"])

    def test_empty_event_list(self):
        result = kind_filter([], kinds=["added"])
        assert list(result) == []
