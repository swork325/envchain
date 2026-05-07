"""Tests for envchain.watcher."""

import os
from typing import List
from unittest.mock import patch

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.watcher import ChangeEvent, EnvWatcher


def _make_chain(*names: str) -> EnvChain:
    chain = EnvChain(profile="test")
    for name in names:
        chain.add(EnvVar(name=name))
    return chain


class TestChangeEvent:
    def test_added_flag(self):
        e = ChangeEvent(key="X", old_value=None, new_value="v")
        assert e.is_added
        assert not e.is_removed
        assert not e.is_modified

    def test_removed_flag(self):
        e = ChangeEvent(key="X", old_value="v", new_value=None)
        assert e.is_removed
        assert not e.is_added

    def test_modified_flag(self):
        e = ChangeEvent(key="X", old_value="a", new_value="b")
        assert e.is_modified

    def test_repr_added(self):
        e = ChangeEvent(key="X", old_value=None, new_value="v")
        assert "added" in repr(e)

    def test_repr_removed(self):
        e = ChangeEvent(key="X", old_value="v", new_value=None)
        assert "removed" in repr(e)

    def test_repr_modified(self):
        e = ChangeEvent(key="X", old_value="a", new_value="b")
        assert "->" in repr(e)


class TestEnvWatcher:
    def test_no_events_when_unchanged(self):
        chain = _make_chain("FOO")
        with patch.dict(os.environ, {"FOO": "bar"}):
            watcher = EnvWatcher(chain)
            watcher._snapshot = watcher._current_values()
            events = watcher.poll_once()
        assert events == []

    def test_detects_value_change(self):
        chain = _make_chain("FOO")
        with patch.dict(os.environ, {"FOO": "old"}):
            watcher = EnvWatcher(chain)
            watcher._snapshot = watcher._current_values()
        with patch.dict(os.environ, {"FOO": "new"}):
            events = watcher.poll_once()
        assert len(events) == 1
        assert events[0].key == "FOO"
        assert events[0].old_value == "old"
        assert events[0].new_value == "new"

    def test_detects_removal(self):
        chain = _make_chain("BAR")
        with patch.dict(os.environ, {"BAR": "present"}):
            watcher = EnvWatcher(chain)
            watcher._snapshot = watcher._current_values()
        env = {k: v for k, v in os.environ.items() if k != "BAR"}
        with patch.dict(os.environ, env, clear=True):
            events = watcher.poll_once()
        assert any(e.key == "BAR" and e.is_removed for e in events)

    def test_handler_called_on_change(self):
        chain = _make_chain("FOO")
        received: List = []
        with patch.dict(os.environ, {"FOO": "v1"}):
            watcher = EnvWatcher(chain)
            watcher._snapshot = watcher._current_values()
        watcher.on_change(lambda evts: received.extend(evts))
        with patch.dict(os.environ, {"FOO": "v2"}):
            watcher.poll_once()
        assert len(received) == 1

    def test_handler_not_called_when_no_change(self):
        chain = _make_chain("FOO")
        called = []
        with patch.dict(os.environ, {"FOO": "same"}):
            watcher = EnvWatcher(chain)
            watcher._snapshot = watcher._current_values()
            watcher.on_change(lambda evts: called.append(evts))
            watcher.poll_once()
        assert called == []
