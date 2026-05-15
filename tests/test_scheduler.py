"""Tests for envchain.scheduler."""

from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock

import pytest

from envchain.chain import EnvChain
from envchain.scheduler import EnvScheduler, ScheduleEntry


def _make_chain() -> EnvChain:
    chain = EnvChain(profile="test")
    chain.add("KEY", "value")
    return chain


class TestScheduleEntry:
    def test_repr_contains_name_and_interval(self):
        entry = ScheduleEntry(name="check", interval=30.0, callback=lambda c: None)
        assert "check" in repr(entry)
        assert "30.0" in repr(entry)

    def test_is_due_when_never_run(self):
        entry = ScheduleEntry(name="x", interval=10.0, callback=lambda c: None)
        assert entry.is_due(time.monotonic())

    def test_not_due_immediately_after_mark(self):
        entry = ScheduleEntry(name="x", interval=60.0, callback=lambda c: None)
        now = time.monotonic()
        entry.mark_ran(now)
        assert not entry.is_due(now + 1.0)

    def test_due_after_interval_elapsed(self):
        entry = ScheduleEntry(name="x", interval=5.0, callback=lambda c: None)
        past = time.monotonic() - 10.0
        entry.mark_ran(past)
        assert entry.is_due(time.monotonic())


class TestEnvScheduler:
    def test_entries_empty_on_init(self):
        scheduler = EnvScheduler(_make_chain())
        assert scheduler.entries == []

    def test_add_registers_entry(self):
        scheduler = EnvScheduler(_make_chain())
        scheduler.add("audit", 10.0, lambda c: None)
        assert len(scheduler.entries) == 1
        assert scheduler.entries[0].name == "audit"

    def test_callback_invoked_within_timeout(self):
        chain = _make_chain()
        received = []
        event = threading.Event()

        def cb(c: EnvChain) -> None:
            received.append(c)
            event.set()

        scheduler = EnvScheduler(chain, tick=0.05)
        scheduler.add("fast", 0.05, cb)
        scheduler.start()
        triggered = event.wait(timeout=2.0)
        scheduler.stop()
        assert triggered
        assert received[0] is chain

    def test_start_twice_raises(self):
        scheduler = EnvScheduler(_make_chain(), tick=0.1)
        scheduler.add("noop", 0.1, lambda c: None)
        scheduler.start()
        with pytest.raises(RuntimeError, match="already running"):
            scheduler.start()
        scheduler.stop()

    def test_stop_joins_thread(self):
        scheduler = EnvScheduler(_make_chain(), tick=0.05)
        scheduler.add("noop", 1.0, lambda c: None)
        scheduler.start()
        scheduler.stop(timeout=2.0)
        assert not scheduler._thread.is_alive()

    def test_callback_exception_does_not_crash_loop(self):
        chain = _make_chain()
        good_event = threading.Event()
        call_count = [0]

        def bad_cb(c: EnvChain) -> None:
            raise ValueError("boom")

        def good_cb(c: EnvChain) -> None:
            call_count[0] += 1
            good_event.set()

        scheduler = EnvScheduler(chain, tick=0.05)
        scheduler.add("bad", 0.05, bad_cb)
        scheduler.add("good", 0.05, good_cb)
        scheduler.start()
        good_event.wait(timeout=2.0)
        scheduler.stop()
        assert call_count[0] >= 1
