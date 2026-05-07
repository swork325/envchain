"""Tests for envchain.cli_watch."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envchain.cli_watch import _format_events, build_parser, run_watch
from envchain.watcher import ChangeEvent


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["some.env"])
        assert args.env_file == "some.env"
        assert args.profile == "dev"
        assert args.interval == 2.0

    def test_custom_profile_and_interval(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--profile", "prod", "--interval", "5"])
        assert args.profile == "prod"
        assert args.interval == 5.0


class TestFormatEvents:
    def test_added_event(self):
        e = ChangeEvent(key="X", old_value=None, new_value="v")
        out = _format_events([e])
        assert "[+]" in out
        assert "X" in out

    def test_removed_event(self):
        e = ChangeEvent(key="Y", old_value="old", new_value=None)
        out = _format_events([e])
        assert "[-]" in out

    def test_modified_event(self):
        e = ChangeEvent(key="Z", old_value="a", new_value="b")
        out = _format_events([e])
        assert "[~]" in out
        assert "->" in out

    def test_multiple_events(self):
        events = [
            ChangeEvent(key="A", old_value=None, new_value="1"),
            ChangeEvent(key="B", old_value="x", new_value=None),
        ]
        out = _format_events(events)
        assert "A" in out
        assert "B" in out


class TestRunWatch:
    def _write_env(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
        tmp.write(content)
        tmp.close()
        return tmp.name

    def test_run_watch_calls_start(self):
        path = self._write_env("FOO=bar\n")
        try:
            with patch("envchain.cli_watch.EnvWatcher") as MockWatcher:
                instance = MagicMock()
                MockWatcher.return_value = instance
                run_watch(path, "dev", 1.0)
                instance.start.assert_called_once()
        finally:
            os.unlink(path)

    def test_run_watch_registers_handler(self):
        path = self._write_env("BAR=baz\n")
        try:
            with patch("envchain.cli_watch.EnvWatcher") as MockWatcher:
                instance = MagicMock()
                MockWatcher.return_value = instance
                run_watch(path, "dev", 1.0)
                instance.on_change.assert_called_once()
        finally:
            os.unlink(path)
